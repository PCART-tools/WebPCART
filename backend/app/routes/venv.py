import os 
import subprocess
import json
from flask import Blueprint, request, jsonify
import tempfile
import shutil
import sys
import logging
import re

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
    try:
        env_type = request.form.get('envType')
        importEnvMethod = request.form.get("importEnvMethod")

        # 创建虚拟环境目录
        env_path = os.path.join(VENV_BASE_PATH, f"{env_type}")
        if os.path.exists(env_path):
            shutil.rmtree(env_path)

        if importEnvMethod == "requirements":   # 使用requirements导入环境
            python_version = request.form.get('pythonVersion', sys.executable)

            # 创建虚拟环境
            result = subprocess.run([python_version, '-m', 'venv', env_path],
                                    capture_output=True, 
                                    text=True)
            if result.returncode != 0:
                return jsonify({
                    "message": f'Failed to create venv: {result.stderr}'
                }), 500
        

            pip_path = os.path.join(env_path, 'Scripts', 'pip.exe') if os.name == 'nt' else os.path.join(env_path, 'bin', 'pip') 
             
            # 升级pip
            result = subprocess.run([pip_path, 'install', '--upgrade', 'pip'],
                                     capture_output=True,
                                    text=True)
            if result.returncode != 0:
                return jsonify({
                    "message": f'Failed to create venv: {result.stderr}'
                }), 500
                
            # 安装setuptools 和 wheel
            setuptools_version = get_setuptools_version(python_version)
            result = subprocess.run([pip_path, 'install', setuptools_version, 'wheel'],
                                        capture_output=True,
                                        text=True)
            if result.returncode != 0:
                    return jsonify({
                        "message": f'Failed to create venv: {result.stderr}'
                    }), 500
            
            # 安装依赖
            requirements = request.files['requirements']
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_req:
                content = requirements.read().decode('utf-8')
                temp_req.write(content)
                req_path = temp_req.name

            result = subprocess.run([pip_path, 'install', '--prefer-binary' , '-r', req_path],
                                    capture_output=True,
                                    text=True)
            os.unlink(req_path)
            if result.returncode != 0:
                logger.error(f'Failed to install dependencies: {result.stderr}')
                logger.error(f'STDOUT: {result.stdout}')
        
                return jsonify({
                    'message': f'Failed to install dependencies: {result.stderr}',
                    'status': 'error'
                }), 500
            
            dependencies = get_packages(pip_path)
            
            return jsonify({
                'status': 'success',
                'path': env_path,
                'dependencies': dependencies,
                'pythonVersion': python_version
                })
        else:
            return jsonify({
                'message': 'Unsupported importEnvMethod',
                'status': 'error'
            })
    except Exception as e:
        return jsonify({
            'message': str(e),
            'status': 'error'
        }), 500
        
    
        