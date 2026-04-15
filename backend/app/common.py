import os
import json
import logging
import shutil
from flask import g, session, request

# 设置日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加载配置文件
config_path = os.path.join(os.path.dirname(__file__), 'config.json')
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

def get_user_id():
    if hasattr(g, 'user_id'):
        return g.user_id
    user_id = session.get('user_id')
    if not user_id:
        import uuid
        user_id = str(uuid.uuid4())
        session['user_id'] = user_id
        g.user_id = user_id
    return user_id


def get_project_base_path():
    user_id = get_user_id()
    base_path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', config['project_base_path'])
    )
    
    user_project_path = os.path.join(base_path, user_id)
    if not os.path.exists(user_project_path):
        os.makedirs(user_project_path, exist_ok=True)
    return user_project_path

def get_project_copy_path():
    user_id = get_user_id()
    base_path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', config['project_copy_path'])
    )
    
    user_copy_path = os.path.join(base_path, user_id)
    if not os.path.exists(user_copy_path):
        os.makedirs(user_copy_path, exist_ok=True)
    return user_copy_path

def get_config_base_path():
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', config['fix_config_base_path'])
    )

def get_env_base_path():
    user_id = get_user_id()
    base_path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', config['env_base_path'])
    )
    
    user_env_path = os.path.join(base_path, user_id)
    if not os.path.exists(user_env_path):
        os.makedirs(user_env_path, exist_ok=True)
    return user_env_path

def get_report_base_path():
    user_id = get_user_id()
    base_path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', config['report_base_path'])
    )
    
    user_report_path = os.path.join(base_path, user_id)
    if not os.path.exists(user_report_path):
        os.makedirs(user_report_path, exist_ok=True)
    return user_report_path

def get_instrument_base_path():
    user_id = get_user_id()
    base_path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', config['project_instrument_path'])
    )
    
    user_instrument_path = os.path.join(base_path, user_id)
    if not os.path.exists(user_instrument_path):
        os.makedirs(user_instrument_path, exist_ok=True)
    return user_instrument_path

def get_work_dir():
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', config['fix_work_dir'])
    )

# def get_report_path():
#     return os.path.join(get_work_dir(), 'Report')

# def get_instrument_path():
#     return os.path.join(get_work_dir(), 'Copy')

def get_conda_path():
    # 使用环境变量查找conda
    conda_path = os.environ.get('CONDA_PATH')
    if conda_path and os.path.exists(conda_path):
        return conda_path
    
    # 检查配置文件中的路径
    configured_path = config['conda_path']
    if os.path.exists(configured_path):
        return configured_path
    
    # 检查常见的conda安装路径
    common_paths = [
        '/opt/conda/bin/conda', 
        '/usr/local/miniconda/bin/conda',
        '/usr/local/anaconda/bin/conda',
        '/home/linuxbrew/.linuxbrew/bin/conda'
    ]
    
    # 检查用户目录下的常见路径
    home_dir = os.path.expanduser("~")
    user_conda_paths = [
        os.path.join(home_dir, "miniconda3", "bin", "conda"),
        os.path.join(home_dir, "anaconda3", "bin", "conda"),
        os.path.join(home_dir, ".local", "miniconda3", "bin", "conda"),
        os.path.join(home_dir, ".local", "anaconda3", "bin", "conda")
    ]
    
    all_paths = common_paths + user_conda_paths
    
    for path in all_paths:
        if os.path.exists(path):
            return path
    
    # 如果所有路径都不存在，返回配置文件中的原始路径
    return configured_path

def clean_directories():
    # 获取基础路径
    base_backend_path = os.path.join(os.path.dirname(__file__), '..')
    base_pcart_path = os.path.normpath(os.path.join(os.path.dirname(__file__), config['fix_work_dir']))
    
    directories_to_clean = [
        os.path.join(base_backend_path, config['project_base_path']),  # ./data/projects
        os.path.join(base_backend_path, config['project_copy_path']),  # ./data/projects_copy
        os.path.join(base_backend_path, config['report_base_path']),   # ./data/reports
        os.path.join(base_backend_path, config['project_instrument_path']),  # ./data/projects_instrument
        os.path.join(base_pcart_path, 'Configure'),  # ../pcart/Configure
        os.path.join(base_pcart_path, 'Copy'),       # ../pcart/Copy
        os.path.join(base_pcart_path, 'Report')      # ../pcart/Report
    ]
    
def clean_directories():
    # 获取基础路径
    base_backend_path = os.path.join(os.path.dirname(__file__), '..')
    base_pcart_path = os.path.normpath(os.path.join(os.path.dirname(__file__), config['fix_work_dir']))
    
    directories_to_clean = [
        os.path.join(base_backend_path, config['project_base_path']), 
        os.path.join(base_backend_path, config['project_copy_path']),  
        os.path.join(base_backend_path, config['report_base_path']),  
        os.path.join(base_backend_path, config['project_instrument_path']), 
        os.path.join(base_pcart_path, 'Configure'),  
        os.path.join(base_pcart_path, 'Copy'),       
        os.path.join(base_pcart_path, 'Report')      
    ]
    
    logger.info("Starting server data cleanup")
    for directory in directories_to_clean:
        if os.path.exists(directory):
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                try:
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.unlink(item_path)  
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)  
                except Exception as e:
                    logger.error(f"Error deleting {item_path}: {e}")
            logger.info(f"Completed cleaning directory: {directory}")
        else:
            logger.warning(f"Directory does not exist, skipping cleanup: {directory}")
