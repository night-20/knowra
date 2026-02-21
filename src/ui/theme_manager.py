from PyQt6.QtWidgets import QApplication
from pathlib import Path
import os
from loguru import logger

class ThemeManager:
    # 使用相对项目根目录的路劲
    THEMES = {
        "dark": "assets/styles/dark.qss",
        "light": "assets/styles/light.qss",
        "claude": "assets/styles/claude.qss"
    }

    @staticmethod
    def apply_theme(theme_name: str = "claude"):
        # 当前工作目录应该是项目根目录
        base_dir = Path(__file__).parent.parent.parent
        path = base_dir / ThemeManager.THEMES.get(theme_name, "assets/styles/claude.qss")
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    qss = f.read()
                    
                    app = QApplication.instance()
                    if app:
                        app.setStyleSheet(qss)
                        logger.info(f"Theme {theme_name} applied successfully.")
            except Exception as e:
                logger.error(f"Failed to apply theme {theme_name}: {e}")
        else:
            logger.warning(f"Theme file not found: {path}. Fallback to generic unstyled mode.")
