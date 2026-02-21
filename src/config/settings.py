import tomllib
import tomli_w
from pathlib import Path
from .constants import (
    CONFIG_FILE, DEFAULT_SETTINGS, APPDATA_DIR, DATA_DIR, 
    VECTOR_DIR, DOCS_DIR, MEDIA_DIR, MODELS_DIR, LOGS_DIR
)

class SettingsManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SettingsManager, cls).__new__(cls)
            cls._instance._init_dirs()
            cls._instance._load()
        return cls._instance
        
    def _init_dirs(self):
        """初始化所有需要的数据目录"""
        dirs = [APPDATA_DIR, DATA_DIR, VECTOR_DIR, DOCS_DIR, MEDIA_DIR, MODELS_DIR, LOGS_DIR]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
            
    def _load(self):
        self.config = DEFAULT_SETTINGS.copy()
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "rb") as f:
                    user_config = tomllib.load(f)
                    self._update_dict(self.config, user_config)
            except Exception as e:
                # 此时 logging 系统可能尚未初始化，但后续可以依赖文件记录
                import logging
                logging.error(f"加载应用配置文件失败: {e}")
                
    def _update_dict(self, base, update):
        for k, v in update.items():
            if isinstance(v, dict) and k in base and isinstance(base[k], dict):
                self._update_dict(base[k], v)
            else:
                base[k] = v
                
    def save(self):
        """将当前配置持久化到 app_data 的 toml 文件"""
        try:
            with open(CONFIG_FILE, "wb") as f:
                tomli_w.dump(self.config, f)
        except Exception as e:
            import logging
            logging.error(f"保存应用配置文件失败: {e}")

    def get(self, section: str, key: str = None, default=None):
        sec = self.config.get(section, {})
        if key is None:
            return sec
        return sec.get(key, default)

    def set(self, section: str, key: str, value):
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        self.save()

# 导出全局单例
settings = SettingsManager()
