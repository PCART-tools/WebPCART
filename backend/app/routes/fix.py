from flask import Blueprint, jsonify, request, send_from_directory, send_file
import os
import json

fix_bp = Blueprint('fix', __name__)

# 读取配置文件
config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

CONFIG_BASE_PATH = os.path.join(os.path.dirname(__file__), '..', '..', config['fix_config_base_path'])

ENV_BASE_PATH = os.path.join(os.path.dirname(__file__), '..', '..', config['env_base_path'])
PROJECT_BASE_PATH = os.path.join(os.path.dirname(__file__), '..', '..', config['project_base_path'])

# 生成配置文件
def generate_fix_config(projectName, selectedLibrary, fix_command, run_file_path):
    current_env = os.path.join(ENV_BASE_PATH, 'current')
    target_env = os.path.join(ENV_BASE_PATH, 'target')
    project = os.path.join(PROJECT_BASE_PATH, projectName)

    config_content = {
        'projPath': project,
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
    try:
        data = request.get_json()

        project_name = data['projectName']
        selected_library = {
            'name': data['libName'],
            'currentVersion': data['currentVersion'],
            'targetVersion': data['targetVersion']
        }
        run_command = data['runCommand']
        run_file_path = data['runFilePath']

        config_file_path = generate_fix_config(project_name, selected_library, run_command, run_file_path)

        return jsonify({
            'status': 'success',
            'message': 'Fix command executed successfully',
            'config_path': config_file_path
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500