import sys
from loguru import logger
from src.config.constants import LOGS_DIR

def setup_logger():
    """配置全局 loguru 日志系统"""
    logger.remove()  # 移除默认的 stderr handler
    
    # 控制台输出 (方便开发时查看)
    logger.add(
        sys.stderr, 
        level="DEBUG", 
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # 文件输出，具备滚动切割策略：单个文件最大 10MB，全局只保留 5 个
    log_file = LOGS_DIR / "app.log"
    logger.add(
        str(log_file),
        rotation="10 MB",
        retention=5,
        level="INFO",
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"
    )
    
    logger.info("Knowra 日志系统初始化完毕")

def setup_excepthook():
    """配置全局异常捕获，确保不漏掉任何奔溃信息"""
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.critical("未捕捉的全局异常", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception
