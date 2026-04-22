import os
import json
import logging
import shutil
from flask import g, session, request
import threading
import time
import subprocess
import pickle

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
    return session.get('user_id')


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

def get_upload_sessions_path():
    base_path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', config['upload_sessions_path'])
    )
    if not os.path.exists(base_path):
        os.makedirs(base_path, exist_ok=True)
    return base_path

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
    
# 初始化时清理所有数据目录
def clean_directories():
    # 获取基础路径
    base_backend_path = os.path.join(os.path.dirname(__file__), '..')
    base_pcart_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..',config['fix_work_dir']))
    
    directories_to_clean = [
        os.path.join(base_backend_path, config['project_base_path']), 
        os.path.join(base_backend_path, config['project_copy_path']),  
        os.path.join(base_backend_path, config['report_base_path']),  
        os.path.join(base_backend_path, config['env_base_path']),
        os.path.join(base_backend_path, config['project_instrument_path']), 
        os.path.join(base_backend_path, config['upload_sessions_path']),
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
            # logger.info(f"Completed cleaning directory: {directory}")
        # else:
        #     logger.warning(f"Directory does not exist, skipping cleanup: {directory}")

# 清理对应目录的过期文件
def clean_old_files(directory, expiry_hours):
    if not os.path.exists(directory):
        return
    
    current_time = time.time()
    expiry_seconds = expiry_hours * 3600
    deleted_count = 0
    
    try:
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            try:
                # 获取文件/目录的最后修改时间
                mtime = os.path.getmtime(item_path)
                if current_time - mtime > expiry_seconds:
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.unlink(item_path)
                        deleted_count += 1
                        logger.info(f"Deleted old file: {item_path}")
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                        deleted_count += 1
                        logger.info(f"Deleted old directory: {item_path}")
            except Exception as e:
                logger.error(f"Error deleting {item_path}: {e}")
        
        if deleted_count > 0:
            logger.info(f"Cleaned {deleted_count} old items from {directory}")
    except Exception as e:
        logger.error(f"Error scanning directory {directory}: {e}")

# 清理过期的上传会话
def cleanup_expired_upload_sessions():
    sessions_dir = get_upload_sessions_path()
    if not os.path.exists(sessions_dir):
        return
        
    now = time.time()
    SESSION_TIMEOUT = 3600  
    RETAIN_TIME_AFTER_FINISH = 300  
    
    expired_ids = []
    active_sessions = []
    
    try:
        for filename in os.listdir(sessions_dir):
            if filename.endswith('.pkl'):
                session_id = filename[:-4]
                active_sessions.append(session_id)
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        return
    
    logger.info(f"Starting upload session cleanup. Current time: {now:.2f}, Active sessions: {active_sessions}")
    
    for sid in active_sessions:
        session_file = os.path.join(sessions_dir, f"{sid}.pkl")
        if not os.path.exists(session_file):
            expired_ids.append(sid)
            continue
            
        try:
            with open(session_file, 'rb') as f:
                session_info = pickle.load(f)
        except Exception as e:
            logger.error(f"Failed to load session {sid}: {e}")
            expired_ids.append(sid)
            continue
            
        session_age = now - session_info['created_at']
        status = session_info.get('status', 'uploading')
        finished_at = session_info.get('finished_at', session_info['created_at'])
        time_since_finish = now - finished_at
        
        logger.info(f"Checking session {sid}: age={session_age:.2f}s, status={status}, time_since_finish={time_since_finish:.2f}s")
        
        # 跳过正在上传的会话
        if 'status' not in session_info or session_info.get('status') == 'uploading':
            if session_age > SESSION_TIMEOUT:
                expired_ids.append(sid)
                logger.info(f"Marking uploading session {sid} for cleanup (age {session_age:.2f}s > timeout {SESSION_TIMEOUT}s)")
            else:
                logger.info(f"Keeping uploading session {sid} (age {session_age:.2f}s <= timeout {SESSION_TIMEOUT}s)")
        # 清理失效的会话
        elif session_info.get('status') in ['completed', 'failed', 'cancelled']:
            if time_since_finish > RETAIN_TIME_AFTER_FINISH:
                expired_ids.append(sid)
                logger.info(f"Marking finished session {sid} for cleanup (time since finish {time_since_finish:.2f}s > retain time {RETAIN_TIME_AFTER_FINISH}s)")
            else:
                logger.info(f"Keeping finished session {sid} (time since finish {time_since_finish:.2f}s <= retain time {RETAIN_TIME_AFTER_FINISH}s)")
    
    if expired_ids:
        logger.info(f"Cleaning up {len(expired_ids)} expired sessions: {expired_ids}")
        for sid in expired_ids:
            # 清理临时文件
            session_file = os.path.join(sessions_dir, f"{sid}.pkl")
            try:
                with open(session_file, 'rb') as f:
                    session_info = pickle.load(f)
                temp_dir = session_info.get('temp_dir')
                if temp_dir and os.path.exists(temp_dir):
                    try:
                        shutil.rmtree(temp_dir, ignore_errors=True)
                        logger.info(f"Removed temp directory for session {sid}: {temp_dir}")
                    except Exception as e:
                        logger.error(f"Failed to remove temp dir {temp_dir}: {e}")
            except Exception as e:
                logger.error(f"Failed to load session info for cleanup {sid}: {e}")
            
            # 删除会话文件
            try:
                if os.path.exists(session_file):
                    os.remove(session_file)
                    logger.info(f"Cleaned up expired upload session: {sid}")
            except Exception as e:
                logger.error(f"Failed to delete session file {sid}: {e}")
    else:
        logger.info("No upload sessions to clean up")

# 定期清理目录
def periodic_cleanup():
    cleanup_interval = config.get('cleanup_interval_hours', 2)
    file_expiry = config.get('file_expiry_hours', 3)
    
    while True:
        try:
            logger.info("Starting periodic cleanup of old files")
            
            # 获取基础路径
            base_backend_path = os.path.join(os.path.dirname(__file__), '..')
            base_pcart_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..",config['fix_work_dir']))
            
            directories_to_clean = [
                os.path.join(base_backend_path, config['project_base_path']), 
                os.path.join(base_backend_path, config['project_copy_path']),  
                os.path.join(base_backend_path, config['report_base_path']),  
                os.path.join(base_backend_path, config['env_base_path']),
                os.path.join(base_backend_path, config['project_instrument_path']), 
                os.path.join(base_backend_path, config['upload_sessions_path']),
                os.path.join(base_pcart_path, 'Configure'),  
                os.path.join(base_pcart_path, 'Copy'),       
                os.path.join(base_pcart_path, 'Report')      
            ]
            
            for directory in directories_to_clean:
                clean_old_files(directory, file_expiry)
            
            # 清理过期的上传会话
            cleanup_expired_upload_sessions()
            
            logger.info("Periodic cleanup completed")
            
            # 等待下一次清理
            time.sleep(cleanup_interval * 3600)
            
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {e}")
            time.sleep(300)  

# 启动清理线程
def start_periodic_cleanup():
    cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
    cleanup_thread.start()
    logger.info("Started periodic cleanup thread")

# 初始化conda配置
def initialize_conda_config():
    try:
        CONDA_PATH = get_conda_path()

        subprocess.run([CONDA_PATH, 'config', '--set', 'anaconda_upload', 'no'], 
                      capture_output=True, text=True)
        subprocess.run([CONDA_PATH, 'tos', 'accept', '--override-channels', '--channel', 'https://repo.anaconda.com/pkgs/main'], 
                       capture_output=True, text=True)
        subprocess.run([CONDA_PATH, 'tos', 'accept', '--override-channels', '--channel', 'https://repo.anaconda.com/pkgs/r'], 
                       capture_output=True, text=True)
        
        logging.info("Conda configuration initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize conda configuration: {str(e)}")