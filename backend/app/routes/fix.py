from flask import Blueprint, jsonify, request, Response
import os
import json
import subprocess
import shutil
import time
from .common import get_logger, get_config_base_path, get_env_base_path, get_project_base_path, get_fixed_project_base_path, get_work_dir

logger = get_logger('fix')
fix_bp = Blueprint('fix', __name__)

# 读取配置文件
CONFIG_BASE_PATH = get_config_base_path()
ENV_BASE_PATH = get_env_base_path()
PROJECT_BASE_PATH = get_project_base_path()
WORK_DIR = get_work_dir()
FIXED_PROJECT_BASE_PATH = get_fixed_project_base_path() 

# 生成配置文件
def generate_fix_config(projectName, selectedLibrary, fix_command, run_file_path, final_project_path):
    current_env = os.path.join(ENV_BASE_PATH, 'current')
    target_env = os.path.join(ENV_BASE_PATH, 'target')
    
    config_content = {
        'projPath': final_project_path,
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
    def generate():
        try:
            # 构建配置文件
            yield f"data: {json.dumps({'status': 'progress', 'step': 'Building the configuration file', 'progress': 10})}\n\n"

            original_project_path = os.path.join(PROJECT_BASE_PATH, project_name)
            final_project_path = os.path.join(FIXED_PROJECT_BASE_PATH, project_name)

            config_file_path = generate_fix_config(project_name, selected_library, run_command, run_file_path, final_project_path)

            # 预处理最终目录
            yield f"data: {json.dumps({'status': 'progress', 'step': 'Preparing project directory', 'progress': 20})}\n\n"
            
            if os.path.exists(final_project_path):
                shutil.rmtree(final_project_path)
                logger.info(f"已清空最终项目路径: {final_project_path}")
            os.makedirs(final_project_path, exist_ok=True)
            
            # 复制原始项目到最终项目目录
            yield f"data: {json.dumps({'status': 'progress', 'step': 'Copying project files', 'progress': 30})}\n\n"
            for item in os.listdir(original_project_path):
                src_path = os.path.join(original_project_path, item)
                dst_path = os.path.join(final_project_path, item)
                if os.path.isdir(src_path):
                    shutil.copytree(src_path, dst_path)
                else:
                    shutil.copy2(src_path, dst_path)
            
            logger.info(f"已将项目从 {original_project_path} 复制到 {final_project_path}")
            
            original_files = set()
            for root, dirs, files in os.walk(final_project_path):
                for file in files:
                    rel_path = os.path.relpath(os.path.join(root, file), final_project_path)
                    original_files.add(rel_path)
            
            yield f"data: {json.dumps({'status': 'progress', 'step': 'Running the repair program', 'progress': 45})}\n\n"
            
            # 构建修复命令
            pcart_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'pcart', 'main.py')
            cmd = [os.sys.executable or 'python', pcart_path, '-cfg', os.path.basename(config_file_path)]
            
            logger.info(f"执行命令: {' '.join(cmd)}")
            logger.info(f"工作目录: {WORK_DIR}")
            
            # 检查配置文件是否存在
            if not os.path.exists(config_file_path):
                error_msg = f"错误: 配置文件不存在 {config_file_path}"
                logger.error(error_msg)
                yield f"data: {json.dumps({'status': 'error', 'message': error_msg})}\n\n"
                return
                
            # 检查PCART程序是否存在
            if not os.path.exists(pcart_path):
                error_msg = f"错误: PCART主文件不存在 {pcart_path}"
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
            
            logger.info(f"修复完成，返回码: {result.returncode}")
            logger.info(f"STDOUT: {result.stdout}")
            if result.stderr:
                logger.error(f"STDERR: {result.stderr}")
            
            if result.returncode == 0:
                logger.info(f"PCART修复成功")
                
                yield f"data: {json.dumps({'status': 'progress', 'step': 'Post-processing results', 'progress': 80})}\n\n"
                
                # 删除原始文件
                for original_file in original_files:
                    file_path = os.path.join(final_project_path, original_file)
                    if os.path.exists(file_path):
                        os.remove(file_path)

                yield f"data: {json.dumps({'status': 'progress', 'step': 'Finalizing results', 'progress': 95})}\n\n"
                time.sleep(0.5)
                
                yield f"data: {json.dumps({'status': 'success', 'message': 'Fix completed successfully', 'progress': 100})}\n\n"
            else:
                error_msg = f"PCART修复失败，返回码: {result.returncode}"
                logger.error(error_msg)
                yield f"data: {json.dumps({'status': 'error', 'message': error_msg})}\n\n"
        except subprocess.TimeoutExpired:
            error_msg = "PCART修复超时"
            logger.error(error_msg)
            yield f"data: {json.dumps({'status': 'error', 'message': error_msg})}\n\n"
        except FileNotFoundError:
            error_msg = "Python解释器或PCART脚本未找到"
            logger.error(error_msg)
            yield f"data: {json.dumps({'status': 'error', 'message': error_msg})}\n\n"
        except Exception as e:
            error_msg = f"执行PCART修复时发生错误: {str(e)}"
            logger.error(error_msg)
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            yield f"data: {json.dumps({'status': 'error', 'message': error_msg})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')