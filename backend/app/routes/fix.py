from flask import Blueprint, jsonify, request, Response
import os
import json
import subprocess
import shutil
import time
from ..common import get_logger, get_config_base_path, get_env_base_path, get_project_base_path, get_project_copy_path, get_work_dir

logger = get_logger('fix')
fix_bp = Blueprint('fix', __name__)

# 读取配置文件
CONFIG_BASE_PATH = get_config_base_path()
ENV_BASE_PATH = get_env_base_path()
PROJECT_BASE_PATH = get_project_base_path()
PROJECT_COPY_PATH = get_project_copy_path()
WORK_DIR = get_work_dir()

# 生成配置文件
def generate_fix_config(projectName, selectedLibrary, fix_command, run_file_path, project_path):
    current_env = os.path.join(ENV_BASE_PATH, 'current')
    target_env = os.path.join(ENV_BASE_PATH, 'target')
    
    config_content = {
        'projPath': project_path,
        'runCommand': fix_command,
        'runFilePath': run_file_path,
        'libName': selectedLibrary['name'],
        'currentVersion': selectedLibrary['currentVersion'],
        'targetVersion': selectedLibrary['targetVersion'],
        'currentEnv': current_env,
        'targetEnv': target_env
    }

    config_file_path = os.path.join(CONFIG_BASE_PATH, f"{projectName}.json")
    os.makedirs(CONFIG_BASE_PATH, exist_ok=True)

    with open(config_file_path, 'w', encoding='utf-8') as f:
        json.dump(config_content, f, ensure_ascii=False, indent=2)

    return config_file_path

@fix_bp.route('/fix/run_fix', methods=['POST'])
def run_fix():
    data = request.get_json()

    project_name = data['projectName']
    selected_library = {
        'name': data['libName'],
        'currentVersion': data['currentVersion'],
        'targetVersion': data['targetVersion']
    }
    run_command = data['runCommand']
    run_file_path = data['runFilePath']
    fix_completed = data.get('fixCompleted', False)

    def generate():
        try:
            # 构建配置文件
            yield f"data: {json.dumps({'status': 'progress', 'step': 'Building the configuration file', 'progress': 10})}\n\n"

            project_path = os.path.join(PROJECT_BASE_PATH, project_name)

            if fix_completed:
                # 获取项目备份
                yield f"data: {json.dumps({'status': 'progress', 'step': 'Restoring project from backup', 'progress': 15})}\n\n"
                
                backup_path = os.path.join(PROJECT_COPY_PATH, project_name)
                if os.path.exists(backup_path):
                    # 删除当前项目目录
                    if os.path.exists(project_path):
                        shutil.rmtree(project_path)
                    
                    # 从备份恢复项目
                    shutil.copytree(backup_path, project_path)
                    logger.info(f"Project restored from backup: {backup_path} -> {project_path}")
                else:
                    error_msg = f"Error: Backup project does not exist {backup_path}"
                    logger.error(error_msg)
                    yield f"data: {json.dumps({'status': 'error', 'message': error_msg})}\n\n"
                    return
            else:
                # 创建项目备份
                yield f"data: {json.dumps({'status': 'progress', 'step': 'Backing up project files', 'progress': 15})}\n\n"

                backup_path = os.path.join(PROJECT_COPY_PATH, project_name)
                if os.path.exists(backup_path):
                    shutil.rmtree(backup_path)
                    logger.info(f"Existing backup directory cleared: {backup_path}")
                
                os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                if os.path.exists(project_path):
                    shutil.copytree(project_path, backup_path)
                    logger.info(f"Project backed up from {project_path} to {backup_path}")
                else:
                    error_msg = f"Error: Original project path does not exist {project_path}"
                    logger.error(error_msg)
                    yield f"data: {json.dumps({'status': 'error', 'message': error_msg})}\n\n"
                    return

            config_file_path = generate_fix_config(project_name, selected_library, run_command, run_file_path, project_path)
            
            yield f"data: {json.dumps({'status': 'progress', 'step': 'Running the repair program', 'progress': 45})}\n\n"
            
            # 构建修复命令
            pcart_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'pcart', 'main.py')
            cmd = [os.sys.executable or 'python', pcart_path, '-cfg', os.path.basename(config_file_path)]
            
            logger.info(f"Executing command: {' '.join(cmd)}")
            logger.info(f"Working directory: {WORK_DIR}")
            
            # 检查配置文件是否存在
            if not os.path.exists(config_file_path):
                error_msg = f"Error: Configuration file does not exist {config_file_path}"
                logger.error(error_msg)
                yield f"data: {json.dumps({'status': 'error', 'message': error_msg})}\n\n"
                return
                
            # 检查PCART程序是否存在
            if not os.path.exists(pcart_path):
                error_msg = f"Error: PCART main file does not exist {pcart_path}"
                logger.error(error_msg)
                yield f"data: {json.dumps({'status': 'error', 'message': error_msg})}\n\n"
                return
            
            # 执行修复程序
            result = subprocess.run(
                cmd,
                cwd=WORK_DIR,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            logger.info(f"Repair completed, return code: {result.returncode}")
            logger.info(f"STDOUT: {result.stdout}")
            if result.stderr:
                logger.error(f"STDERR: {result.stderr}")
            
            if result.returncode == 0:
                logger.info(f"PCART repair successful")
                
                yield f"data: {json.dumps({'status': 'progress', 'step': 'Post-processing results', 'progress': 80})}\n\n"
                
                yield f"data: {json.dumps({'status': 'progress', 'step': 'Finalizing results', 'progress': 95})}\n\n"
                time.sleep(0.5)
                
                yield f"data: {json.dumps({'status': 'success', 'message': 'Fix completed successfully', 'progress': 100})}\n\n"
            else:
                error_msg = f"PCART repair failed, return code: {result.returncode}"
                logger.error(error_msg)
                yield f"data: {json.dumps({'status': 'error', 'message': error_msg})}\n\n"
        except subprocess.TimeoutExpired:
            error_msg = "PCART repair timeout"
            logger.error(error_msg)
            yield f"data: {json.dumps({'status': 'error', 'message': error_msg})}\n\n"
        except FileNotFoundError:
            error_msg = "Python interpreter or PCART script not found"
            logger.error(error_msg)
            yield f"data: {json.dumps({'status': 'error', 'message': error_msg})}\n\n"
        except Exception as e:
            error_msg = f"Error occurred during PCART repair: {str(e)}"
            logger.error(error_msg)
            import traceback
            logger.error(f"Detailed error information: {traceback.format_exc()}")
            yield f"data: {json.dumps({'status': 'error', 'message': error_msg})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')