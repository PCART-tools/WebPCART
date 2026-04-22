import os 
import subprocess
import json
from flask import Blueprint, request, jsonify, Response
import tempfile
import shutil
import sys
import logging
import re
import time
import threading
from ..common import get_logger, get_env_base_path, get_conda_path, get_user_id

logger = get_logger('venv')

venv_bp = Blueprint('venv', __name__)

_user_locks = {}
_locks_mutex = threading.Lock()

_upload_sessions = {}
_sessions_lock = threading.Lock()

def get_user_lock(user_id):
    with _locks_mutex:
        if user_id not in _user_locks:
            _user_locks[user_id] = threading.Lock()
        return _user_locks[user_id]

# 读取配置文件
def get_config():
    ENV_BASE_PATH = get_env_base_path()
    CONDA_PATH = get_conda_path()
    return ENV_BASE_PATH, CONDA_PATH

# 获取已安装的依赖列表
def get_packages(env_path, conda_path):
    try:
        result = subprocess.run([conda_path, 'list', '-p', env_path, '--json'],
                                capture_output=True,
                                text=True)
        if result.returncode == 0:
            packages_data = json.loads(result.stdout)
            dependencies = [f"{pkg['name']}={pkg['version']}" for pkg in packages_data]
            return dependencies
        else:
            logger.error(f'Failed to get installed packages: {result.stderr}')
            return []
    except Exception as e:
        logger.error(f'Failed to get installed packages: {str(e)}')
        return []

# 获取python版本
def get_python_version(env_path, conda_path):
    python_exe = os.path.join(env_path, 'Scripts', 'python.exe') if os.name == 'nt' else os.path.join(env_path, 'bin', 'python')
    if os.path.exists(python_exe):
        result = subprocess.run([python_exe, '--version'],
                                capture_output=True,
                                text=True)
        
        if result.returncode == 0:
            python_version = result.stdout.strip()
        else:
            python_version = 'Unknown'
    else:
        python_version = 'Unknown'

    return python_version


# 采用condapack上传虚拟环境

# 初始化上传会话
@venv_bp.route('/venv/init_upload', methods=['POST'])
def init_upload():
    try:
        data = request.get_json()
        filename = data.get('filename')
        file_size = data.get('fileSize')
        total_chunks = data.get('totalChunks')
        env_type = data.get('envType')

        user_id = get_user_id()
        upload_session_id = f"{user_id}_{int(time.time())}_{filename}"

        temp_dir = tempfile.mkdtemp(prefix=f'upload_{upload_session_id}_')

        with _sessions_lock:
            _upload_sessions[upload_session_id] = {
                'user_id': user_id,
                'filename': filename,
                'file_size': file_size,
                'total_chunks': total_chunks,
                'env_type': env_type,
                'temp_dir': temp_dir,
                'uploaded_chunks': set(),
                'created_at': time.time()
            }

        logger.info(f'Upload session initialized: {upload_session_id}')

        return jsonify({
            'uploadSessionId': upload_session_id,
            'message': 'Upload session created'
        })
    except Exception as e:
        logger.error(f'Failed to initialize upload: {str(e)}')
        return jsonify({'error': str(e)}), 500
    
# 上传分片
@venv_bp.route('/venv/upload_chunk', methods=['POST'])
def upload_chunk():
    try:
        upload_session_id = request.form.get('uploadSessionId')
        chunk_index = int(request.form.get('chunkIndex'))
        total_chunks = int(request.form.get('totalChunks'))
        chunk_file = request.files['chunk']
        
        if not upload_session_id or chunk_index is None:
            return jsonify({'error': 'Missing required fields'}), 400
        
        with _sessions_lock:
            if upload_session_id not in _upload_sessions:
                return jsonify({'error': 'Invalid upload session'}), 404
            
            session = _upload_sessions[upload_session_id]
            
            # 检查是否已上传
            if chunk_index in session['uploaded_chunks']:
                progress = len(session['uploaded_chunks']) / session['total_chunks'] * 100
                return jsonify({
                    'message': 'Chunk already uploaded',
                    'chunkIndex': chunk_index,
                    'progress': progress
                })
            
            # 保存分片文件
            chunk_path = os.path.join(session['temp_dir'], f'chunk_{chunk_index:06d}')
            chunk_data = chunk_file.stream.read()
            with open(chunk_path, 'wb') as f:
                f.write(chunk_data)
            
            session['uploaded_chunks'].add(chunk_index)
            progress = len(session['uploaded_chunks']) / session['total_chunks'] * 100
            uploaded_chunks_count = len(session['uploaded_chunks'])
        
        return jsonify({
            'message': 'Chunk uploaded successfully',
            'chunkIndex': chunk_index,
            'progress': progress,
            'uploadedChunks': uploaded_chunks_count,
            'totalChunks': total_chunks
        })
    
    except Exception as e:
        logger.error(f"Failed to upload chunk: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
# 完成分片上传并合并
@venv_bp.route('/venv/complete_upload', methods=['POST'])
def complete_upload():
    try:
        data = request.get_json()
        upload_session_id = data.get('uploadSessionId')
        env_type = data.get('envType')
        
        if not upload_session_id:
            return jsonify({'error': 'Missing upload session ID'}), 400
        
        with _sessions_lock:
            if upload_session_id not in _upload_sessions:
                return jsonify({'error': 'Invalid upload session'}), 404
            
            session = _upload_sessions[upload_session_id]
            
            # 验证所有分片都已上传
            if len(session['uploaded_chunks']) != session['total_chunks']:
                missing = set(range(session['total_chunks'])) - session['uploaded_chunks']
                return jsonify({
                    'error': 'Incomplete upload',
                    'missingChunks': list(missing)
                }), 400
            
            temp_dir = session['temp_dir']
            total_chunks = session['total_chunks']
        
        ENV_BASE_PATH, CONDA_PATH = get_config()
        env_path = os.path.join(ENV_BASE_PATH, env_type)
        
        def generate_progress():
            session_cleaned = False
            try:
                yield f"data: {json.dumps({'status':'progress', 'step':'Merging chunks', 'progress':5, 'type':env_type})}\n\n"
                
                # 合并分片文件
                merged_path = os.path.join(temp_dir, 'merged.tar.gz')
                with open(merged_path, 'wb') as outfile:
                    for i in range(total_chunks):
                        chunk_path = os.path.join(temp_dir, f'chunk_{i:06d}')
                        with open(chunk_path, 'rb') as infile:
                            shutil.copyfileobj(infile, outfile)
                
                yield f"data: {json.dumps({'status':'progress', 'step':'Chunks merged', 'progress':20, 'type':env_type})}\n\n"
                
                # 验证合并后的文件完整性
                expected_size = session['file_size']
                actual_size = os.path.getsize(merged_path)
                if actual_size != expected_size:
                    logger.error(f"File size mismatch: expected {expected_size}, got {actual_size}, difference: {actual_size - expected_size}")
                    yield f"data: {json.dumps({'status':'error', 'message': f'File size mismatch: expected {expected_size}, got {actual_size} (diff: {actual_size - expected_size})', 'type':env_type})}\n\n"
                    return
                
                # 删除旧环境
                if os.path.exists(env_path):
                    yield f"data: {json.dumps({'status':'progress', 'step':'Removing existing environment', 'progress':30, 'type':env_type})}\n\n"
                    shutil.rmtree(env_path)
                
                os.makedirs(env_path, exist_ok=True)
                
                # 解压
                yield f"data: {json.dumps({'status':'progress', 'step':'Extracting conda pack', 'progress':40, 'type':env_type})}\n\n"
                
                result = subprocess.run(
                    ['tar', '-xzf', merged_path, '-C', env_path],
                    capture_output=True, 
                    text=True,
                    timeout=600
                )
                
                if result.returncode != 0:
                    yield f"data: {json.dumps({'status':'error', 'message': f'Failed to extract: {result.stderr}', 'type':env_type})}\n\n"
                    return
                
                # 清理临时文件
                yield f"data: {json.dumps({'status':'progress', 'step':'Cleaning up', 'progress':80, 'type':env_type})}\n\n"
                shutil.rmtree(temp_dir, ignore_errors=True)
                session_cleaned = True
                
                with _sessions_lock:
                    if upload_session_id in _upload_sessions:
                        del _upload_sessions[upload_session_id]
                
                # 获取环境信息
                dependencies = get_packages(env_path, CONDA_PATH)
                version = get_python_version(env_path, CONDA_PATH)
                
                yield f"data: {json.dumps({'status':'progress', 'step':'Finalizing', 'progress':95, 'type':env_type})}\n\n"
                
                result_data = {
                    'status': 'success',
                    'path': env_path,
                    'dependencies': dependencies,
                    'pythonVersion': version,
                    'type': env_type
                }
                yield f"data: {json.dumps(result_data)}\n\n"
                
            except Exception as e:
                logger.error(f"Failed to complete upload: {str(e)}")
                yield f"data: {json.dumps({'status':'error', 'message': f'Exception: {str(e)}', 'type':env_type})}\n\n"
            finally:
                # 确保清理临时目录
                if not session_cleaned:
                    with _sessions_lock:
                        if upload_session_id in _upload_sessions:
                            session_data = _upload_sessions[upload_session_id]
                            shutil.rmtree(session_data['temp_dir'], ignore_errors=True)
                            del _upload_sessions[upload_session_id]
        
        return Response(generate_progress(), mimetype='text/event-stream')
    
    except Exception as e:
        logger.error(f"Failed to complete upload: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
# 取消上传会话
@venv_bp.route('/venv/cancel_upload', methods=['POST'])
def cancel_upload():
    try:
        data = request.get_json()
        upload_session_id = data.get('uploadSessionId')
        
        if not upload_session_id:
            return jsonify({'error': 'Missing upload session ID'}), 400
        
        with _sessions_lock:
            if upload_session_id in _upload_sessions:
                session = _upload_sessions[upload_session_id]
                shutil.rmtree(session['temp_dir'], ignore_errors=True)
                del _upload_sessions[upload_session_id]
                logger.info(f"Upload session cancelled: {upload_session_id}")
                return jsonify({'message': 'Upload cancelled'})
            else:
                return jsonify({'error': 'Invalid upload session'}), 404
    
    except Exception as e:
        logger.error(f"Failed to cancel upload: {str(e)}")
        return jsonify({'error': str(e)}), 500

def get_python_version(env_path, conda_path):
    python_exe = os.path.join(env_path, 'Scripts', 'python.exe') if os.name == 'nt' else os.path.join(env_path, 'bin', 'python')
    if os.path.exists(python_exe):
        result = subprocess.run([python_exe, '--version'],
                                capture_output=True,
                                text=True)
        
        if result.returncode == 0:
            python_version = result.stdout.strip()
        else:
            python_version = 'Unknown'
    else:
        python_version = 'Unknown'

    return python_version


# 采用requirements.txt上传虚拟环境

# 获取requirements中的包列表
def parse_requirements(requirements_content):
    packages = []
    for line in requirements_content.splitlines():
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('-'):
            packages.append(line)
    return packages

# 使用pip安装依赖
def install_with_pip(env_path, requirements_content):
    try:
        python_exe = os.path.join(env_path, 'Scripts', 'python.exe') if os.name == 'nt' else os.path.join(env_path, 'bin', 'python')
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_req:
            temp_req.write(requirements_content)
            req_path = temp_req.name
        
        try:            
            result = subprocess.run(
                [python_exe, '-m', 'pip', 'install', '-r', req_path, 
                 '-i', 'https://pypi.tuna.tsinghua.edu.cn/simple',
                 '--no-input', '--no-cache-dir'],
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode != 0:
                logger.error(f"Pip install failed: {result.stderr}")
                return False, result.stderr
            
            return True, None
        finally:
            os.unlink(req_path)
    except Exception as e:
        logger.error(f"Pip installation error: {str(e)}")
        return False, str(e)

# 使用conda安装依赖
def install_with_conda(env_path, requirements_content, conda_path):
    packages = parse_requirements(requirements_content)
    
    if not packages:
        return True, None
    
    temp_conda_dir = tempfile.mkdtemp(prefix='conda_install_')
    
    try:
        env_vars = os.environ.copy()
        env_vars['CONDA_CHANNELS'] = 'https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge,https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main,defaults'
        env_vars['CONDA_AUTO_UPDATE_CONDA'] = 'false'
                
        conda_packages = []
        pip_packages = []
        
        # 分析那些包使用conda下载
        for pkg in packages:
            clean_name = re.split(r'[><=!]', pkg)[0]
            if clean_name.startswith(('http', 'git+', 'svn+')) or '.' in clean_name:
                pip_packages.append(pkg)
            else:
                conda_packages.append(pkg)
        
        # 安装conda包
        if conda_packages:
            cmd = [conda_path, 'install', '-p', env_path, '-y'] + conda_packages + [
                '-c', 'conda-forge', 
                '--quiet',
                '--no-deps'
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, env=env_vars, timeout=600)

                
            if result.returncode != 0:
                logger.warning(f"Failed to install batch with conda: {result.stderr[:200]}")
                pip_packages.extend(conda_packages)
        
        if pip_packages:
            success, error = install_with_pip(env_path, '\n'.join(pip_packages))
            if not success:
                return False, error
        
        return True, None
        
    except Exception as e:
        logger.error(f"Optimized conda install error: {str(e)}")
        return False, str(e)
    finally:
        try:
            shutil.rmtree(temp_conda_dir, ignore_errors=True)
        except Exception as e:
            logger.warning(f"Failed to cleanup temp dir: {e}")

# 创建虚拟环境
@venv_bp.route('/venv/create', methods=['POST'])
def create_venv():
    env_type = request.form.get('envType')
    importEnvMethod = request.form.get("importEnvMethod")
    python_version = request.form.get('pythonVersion', 'python3.9')

    user_id = get_user_id()
    user_lock = get_user_lock(user_id)

    if importEnvMethod == 'requirements':
        requirements_file = request.files['requirements']
        requirements_content = requirements_file.read().decode('utf-8')
    else:
        return jsonify({'error': 'Unsupported importEnvMethod'}), 400

    ENV_BASE_PATH, CONDA_PATH = get_config()

    def generate_progress():
        try:
            # 初始化虚拟环境
            yield f"data: {json.dumps({'status':'progress', 'step':'Initializing', 'progress':5, 'type':env_type})}\n\n"
            
            env_path = os.path.join(ENV_BASE_PATH, f"{env_type}")
            
            # 移除已有虚拟环境
            if os.path.exists(env_path):
                yield f"data: {json.dumps({'status':'progress', 'step':'Removing existing environment', 'progress':10, 'type':env_type})}\n\n"
                shutil.rmtree(env_path, ignore_errors=True)

            python_version_num = python_version.replace('python', '')
            
            yield f"data: {json.dumps({'status':'progress', 'step':'Creating conda environment', 'progress':15, 'type':env_type})}\n\n"

            temp_conda_dir = tempfile.mkdtemp(prefix=f'conda_create_{user_id}_')
            temp_pkgs_dir = os.path.join(temp_conda_dir, 'pkgs')
            os.makedirs(temp_pkgs_dir, exist_ok=True)

            try:
                env_vars = os.environ.copy()
                env_vars['CONDA_PKGS_DIRS'] = temp_pkgs_dir
                env_vars['CONDA_CHANNELS'] = 'https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge,defaults'
                env_vars['CONDA_AUTO_UPDATE_CONDA'] = 'false'
                
                with user_lock:
                    result = subprocess.run(
                        [CONDA_PATH, 'create', '-y', '-p', env_path, f'python={python_version_num}', '--quiet'],
                        capture_output=True, 
                        text=True,
                        env=env_vars,
                        timeout=300
                    )
                    
                    if result.returncode != 0:
                        yield f"data: {json.dumps({'status':'error', 'message': f'Failed to create environment: {result.stderr}', 'type':env_type})}\n\n"
                        return

            except subprocess.TimeoutExpired:
                yield f"data: {json.dumps({'status':'error', 'message': 'Environment creation timed out', 'type':env_type})}\n\n"
                return
            finally:
                try:
                    shutil.rmtree(temp_conda_dir, ignore_errors=True)
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp dir: {e}")

            yield f"data: {json.dumps({'status':'progress', 'step':'Conda environment created', 'progress':25, 'type':env_type})}\n\n"

            # 安装依赖
            yield f"data: {json.dumps({'status':'progress', 'step':'Installing dependencies', 'progress':28, 'type':env_type})}\n\n"
            
            success, error = install_with_conda(env_path, requirements_content, CONDA_PATH)
            
            if not success:
                yield f"data: {json.dumps({'status':'progress', 'step':'Falling back to pip installation', 'progress':30, 'type':env_type})}\n\n"
                
                success, error = install_with_pip(env_path, requirements_content)
                
                if not success:
                    yield f"data: {json.dumps({'status':'error', 'message': f'Failed to install dependencies: {error}', 'type':env_type})}\n\n"
                    return

            yield f"data: {json.dumps({'status':'progress', 'step':'Finalizing environment', 'progress':95, 'type':env_type})}\n\n"
            
            dependencies = get_packages(env_path, CONDA_PATH)
            version = get_python_version(env_path, CONDA_PATH)
            
            result_data = {
                'status': 'success',
                'path': env_path,
                'dependencies': dependencies,
                'pythonVersion': version,
                'type': env_type
            }

            yield f"data: {json.dumps(result_data)}\n\n"  
            
        except Exception as e:
            logger.error(f'Failed to create environment: {str(e)}')
            yield f"data: {json.dumps({'status':'error', 'message': f'Exception during environment creation: {str(e)}', 'type':env_type})}\n\n"
    
    return Response(generate_progress(), mimetype='text/event-stream')    
        