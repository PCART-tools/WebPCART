import os
import json
import logging
import shutil

# 设置日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加载配置文件
config_path = os.path.join(os.path.dirname(__file__), 'config.json')
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

def get_project_base_path():
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', '..', config['project_base_path'])
    )

def get_fixed_project_base_path():
     return os.path.normpath(
         os.path.join(os.path.dirname(__file__), '..', '..', config['fixed_project_base_path'])
     )

def get_config_base_path():
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', '..', config['fix_config_base_path'])
    )

def get_env_base_path():
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', '..', config['env_base_path'])
    )

def get_work_dir():
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', '..', config['fix_work_dir'])
    )

def get_conda_path():
        return config['conda_path']

required_dirs = [
    get_project_base_path(),
    get_config_base_path(),
    get_env_base_path(), 
]

# 检查并初始化数据目录
def initialize_directories():
    for directory in required_dirs:
        if not os.path.exists(directory):
            # 目录不存在，创建目录
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Created directory: {directory}")
        else:
            # 目录存在，清空目录内容
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            logger.info(f"Cleared directory: {directory}")

initialize_directories()