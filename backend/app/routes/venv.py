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

# 读取配置文件
config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

ENV_BASE_PATH = os.path.join(os.path.dirname(__file__), '..', '..', config['env_base_path'])
CONDA_PATH = config['conda_path']

# 获取已安装的依赖列表
def get_packages(env_path):
    try:
        result = subprocess.run([CONDA_PATH, 'list', '-p', env_path, '--json'],
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
            yield f"data: {json.dumps({'status':'progress', 'step':'Initializing', 'progress':5, 'type':env_type})}\n\n"
            time.sleep(0.5)

            # 创建虚拟环境目录
            env_path = os.path.join(ENV_BASE_PATH, f"{env_type}")
            if os.path.exists(env_path):
                yield f"data: {json.dumps({'status':'progress', 'step':'Removing existing environment', 'progress':10, 'type':env_type})}\n\n"
                time.sleep(0.5)

                subprocess.run([CONDA_PATH, 'env', 'remove', '-y', '-p', env_path], capture_output=True)

            if importEnvMethod == "requirements":   # 使用requirements导入环境
                # 创建虚拟环境
                yield f"data: {json.dumps({'status':'progress', 'step':'Creating conda environment', 'progress':15, 'type':env_type})}\n\n"

                python_version_num = python_version.replace('python', '')   # 提取版本号

                result = subprocess.run([CONDA_PATH, 'create', '-y', '-p', env_path, f'python={python_version_num}'],
                                        capture_output=True, 
                                        text=True)
                if result.returncode != 0:
                    yield f"data: {json.dumps({'status':'error', 'message': f'Failed to create environment: {result.stderr}'})}\n\n"
                    return

                yield f"data: {json.dumps({'status':'progress', 'step':'Conda envrionment created', 'progress':25, 'type':env_type})}\n\n"
                time.sleep(0.5)

                yield f"data: {json.dumps({'status':'progress', 'step':'Installing dependencies', 'progress':30, 'type':env_type})}\n\n"
                
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_req:
                    temp_req.write(requirements_content)
                    req_path = temp_req.name
                
                result = subprocess.run([CONDA_PATH, 'install', '-p', env_path, '--file', req_path, '-y'],
                                        capture_output=True, text=True)
                
                if result.returncode != 0:
                    os.unlink(req_path)
                    yield f"data: {json.dumps({'status':'error', 'message': f'Failed to install dependencies: {result.stderr}', 'type':env_type})}\n\n"
                    return

                os.unlink(req_path)

                yield f"data: {json.dumps({'status':'progress', 'step':'Dependencies installed', 'progress':90, 'type':env_type})}\n\n"
                time.sleep(0.5)
                

                yield f"data: {json.dumps({'status':'progress', 'step':'Finalizing', 'progress':95, 'type':env_type})}\n\n"
                
                dependencies = get_packages(env_path)
                
                result_data = {
                    'status': 'success',
                    'path': env_path,
                    'dependencies': dependencies,
                    'pythonVersion': python_version,
                    'type': env_type
                }

                yield f"data: {json.dumps(result_data)}\n\n"     
            else:
                yield f"data: {json.dumps({'status':'error', 'message': 'Unsupported importEnvMethod', 'type':env_type})}\n\n"
        except Exception as e:
            logger.error(f'Failed to create: {str(e)}')

            yield f"data: {json.dumps({'status':'error', 'message': f'Exception during environment creation: {str(e)}', 'type':env_type})}\n\n"
    return Response(generate_progress(), mimetype='text/event-stream')
        
    
        