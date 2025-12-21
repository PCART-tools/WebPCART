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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

venv_bp = Blueprint('venv', __name__)

VENV_BASE_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'venv')
os.makedirs(VENV_BASE_PATH, exist_ok=True)

# 根据python版本获取setuptools
def get_setuptools_version(python_version):
    version_match = re.search(r'python(\d+\.\d+)', python_version)
    version = version_match.group(1)
    major, minor = map(int, version.split('.'))

    if major > 3 or (major == 3 and minor >= 12):   # Python 3.12及以上
        return "setuptools>=65.5.0"
    elif major == 3 and minor >= 10:    # Python 3.10及以上
        return "setuptools>=58.0.0,<66.0.0"
    else:   # 其他版本
        return "setuptools"
    
# 获取已安装的依赖列表
def get_packages(pip_path):
    try:
        result = subprocess.run([pip_path, 'freeze'],
                                capture_output=True,
                                text=True)
        if result.returncode == 0:
            dependencies = result.stdout.strip().split('\n')
            dependencies = [dep for dep in dependencies if dep]
            return dependencies
        else:
            logger.error(f'Failed to get installed packages: {result.stderr}')
            return []
    except Exception as e:
        logger.error(f'Failed to get installed packages: {str(e)}')
        return []


# 创建虚拟环境
@venv_bp.route('/venv/create', methods=['POST'])
def create_venv():
    env_type = request.form.get('envType')
    importEnvMethod = request.form.get("importEnvMethod")
    python_version = request.form.get('pythonVersion', sys.executable)

    requirements_content = None
    if 'requirements' in request.files:
        requirements_file = request.files['requirements']
        requirements_content = requirements_file.read().decode('utf-8')
    def generate_progress():
        try:
            yield f"data: {json.dumps({'status':'progress', 'step':'Initializing', 'progress':5})}\n\n"
            time.sleep(0.5)

            # 创建虚拟环境目录
            env_path = os.path.join(VENV_BASE_PATH, f"{env_type}")
            if os.path.exists(env_path):
                yield f"data: {json.dumps({'status':'progress', 'step':'Removing existing environment', 'progress':10})}\n\n"
                time.sleep(0.5)

                shutil.rmtree(env_path)

            if importEnvMethod == "requirements":   # 使用requirements导入环境
                # 创建虚拟环境
                yield f"data: {json.dumps({'status':'progress', 'step':'Creating virtual environment', 'progress':15})}\n\n"

                result = subprocess.run([python_version, '-m', 'venv', env_path],
                                        capture_output=True, 
                                        text=True)
                if result.returncode != 0:
                    yield f"data: {json.dumps({'status':'error', 'message': f'Failed to create: {result.stderr}'})}\n\n"
                    return

                yield f"data: {json.dumps({'status':'progress', 'step':'Virtual envrionment created', 'progress':25})}\n\n"
                time.sleep(0.5)

                pip_path = os.path.join(env_path, 'Scripts', 'pip.exe') if os.name == 'nt' else os.path.join(env_path, 'bin', 'pip') 
                
                # 升级pip
                yield f"data: {json.dumps({'status':'progress', 'step':'Upgrading pip', 'progress':30})}\n\n"

                result = subprocess.run([pip_path, 'install', '--upgrade', 'pip'],
                                        capture_output=True,
                                        text=True)
                if result.returncode != 0:
                    yield f"data: {json.dumps({'status':'error', 'message': f'Failed to upgrade pip: {result.stderr}'})}\n\n"
                    return
                
                yield f"data: {json.dumps({'status':'progress', 'step':'Pip upgraded', 'progress':40})}\n\n"
                time.sleep(0.5)
                    
                # 安装setuptools 和 wheel
                yield f"data: {json.dumps({'status':'progress', 'step':'Installing setuptools and wheel', 'progress':45})}\n\n"

                setuptools_version = get_setuptools_version(python_version)
                result = subprocess.run([pip_path, 'install', setuptools_version, 'wheel'],
                                            capture_output=True,
                                            text=True)
                if result.returncode != 0:
                    yield f"data: {json.dumps({'status':'error', 'message': f'Failed to install setuptools and wheel: {result.stderr}'})}\n\n"
                    return
                
                yield f"data: {json.dumps({'status':'progress', 'step':'Setuptools and wheel installed', 'progress':55})}\n\n"
                time.sleep(0.5)
                
                # 安装依赖
                yield f"data: {json.dumps({'status':'progress', 'step':'Installing dependencies', 'progress':60})}\n\n"

                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_req:
                    temp_req.write(requirements_content)
                    req_path = temp_req.name

                result = subprocess.run([pip_path, 'install', '--prefer-binary' , '-r', req_path],
                                        capture_output=True,
                                        text=True)
                os.unlink(req_path)
                if result.returncode != 0:
                    logger.error(f'Failed to install dependencies: {result.stderr}')
                    logger.error(f'STDOUT: {result.stdout}')
            
                    yield f"data: {json.dumps({'status':'error', 'message': f'Failed to install dependencies: {result.stderr}'})}\n\n"
                    return
                
                yield f"data: {json.dumps({'status':'progress', 'step':'Dependencies installed', 'progress':90})}\n\n"
                
                dependencies = get_packages(pip_path)

                yield f"data: {json.dumps({'status':'progress', 'step':'Finalizing', 'progress':95})}\n\n"
                time.sleep(0.5)
                
                result_data = {
                    'status': 'success',
                    'path': env_path,
                    'dependencies': dependencies,
                    'pythonVersion': python_version
                }

                yield f"data: {json.dumps(result_data)}\n\n"     
            else:
                yield f"data: {json.dumps({'status':'error', 'message': 'Unsupported importEnvMethod'})}\n\n"
        except Exception as e:
            logger.error(f'Failed to create: {str(e)}')

            yield f"data: {json.dumps({'status':'error', 'message': f'Exception during environment creation: {str(e)}'})}\n\n"
    return Response(generate_progress(), mimetype='text/event-stream')
        
    
        