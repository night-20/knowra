import sys
from PyQt6.QtWidgets import QApplication
from loguru import logger
from src.ui.main_window import MainWindow
from src.ui.theme_manager import ThemeManager
from src.ui.widgets.toast import ToastNotification
from src.models import init_db

class KnowraApp:
    def __init__(self, argv):
        self.app = QApplication(argv)
        self._setup_exception_hook()
        
        # 初始化数据库字典
        init_db()
        
        # 加载样式表
        ThemeManager.apply_theme("dark")
        
        self.main_window = MainWindow()
        
    def _setup_exception_hook(self):
        """全局异常劫持"""
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
                
            logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
            
            # 使用 Toast 显示严重错误
            msg = f"系统发生异常: {exc_value}"
            ToastNotification.show_toast(msg, toast_type="error")
            
        sys.excepthook = handle_exception

    def run(self):
        self.main_window.show()
        return self.app.exec()
