import threading
import os
from loguru import logger
from pathlib import Path


def custom_logger_filter(record):
    """为log添加额外参数"""
    # 添加request_id
    try:
        request_id = threading.current_thread().name
        record["extra"]["request_id"] = request_id
    except Exception as e:
        print(f"Error adding request_id to log record: {e}")
    
    # 计算当前文件相对于项目根目录的路径
    try:
        base_dir = Path(__file__).resolve().parent.parent
        file_path = str(record["file"].path)
        relative_path = os.path.relpath(file_path, base_dir)
        # 将路径分隔符替换为 "."
        relative_path = relative_path.replace(os.sep, ".")
        record["extra"]["relative_path"] = relative_path
    except Exception as e:
        print(f"Error adding relative_path to log record: {e}")
    return True


logger.add(
    "logs/loguru/django_request_{time:YYYY-MM-DD}.log",
    colorize=True,
    rotation="1 day",
    retention="30 days",
    enqueue=True,
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | "
            "{extra[request_id]} | "
            "{level:<8} | "
            "{extra[relative_path]}:{function}:{line} - "
            "{message}",

    filter=custom_logger_filter
)
