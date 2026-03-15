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
        os.path.join(os.path.dirname(__file__), '..', config['project_base_path'])
    )

def get_project_copy_path():
     return os.path.normpath(
         os.path.join(os.path.dirname(__file__), '..', config['project_copy_path'])
     )

def get_config_base_path():
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', config['fix_config_base_path'])
    )

def get_env_base_path():
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', config['env_base_path'])
    )

def get_work_dir():
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', config['fix_work_dir'])
    )

def get_report_path():
    return os.path.join(get_work_dir(), 'Report')

def get_instrument_path():
    return os.path.join(get_work_dir(), 'Copy')

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

required_dirs = [
    get_project_base_path(),
    get_project_copy_path(),
    get_config_base_path(),
    get_env_base_path(), 
    get_report_path(),
    get_instrument_path()
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
            try:
                for item in os.listdir(directory):
                    item_path = os.path.join(directory, item)
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                logger.info(f"Cleared directory: {directory}")
            except Exception as e:
                logger.warning(f"Could not clear directory {directory}: {str(e)}")


initialize_directories()