import os
from pathlib import Path

APP_NAME = "Knowra"
APP_VERSION = "1.0.0"

# 获取 APPDATA 目录
if os.name == 'nt':
    # Windows
    APPDATA_DIR = Path(os.getenv('APPDATA', os.path.expanduser('~'))) / APP_NAME
else:
    # Linux/Mac fallback
    APPDATA_DIR = Path(os.path.expanduser('~')) / f".{APP_NAME}"

# 核心系统目录
CONFIG_FILE = APPDATA_DIR / "config.toml"
DATA_DIR = APPDATA_DIR / "databases"
VECTOR_DIR = APPDATA_DIR / "vectorstore"
DOCS_DIR = APPDATA_DIR / "documents"
MEDIA_DIR = APPDATA_DIR / "media"
MODELS_DIR = APPDATA_DIR / "models"
LOGS_DIR = APPDATA_DIR / "logs"

# 默认设置参数
DEFAULT_SETTINGS = {
    "app": {
        "theme": "dark",
        "geometry": None
    },
    "llm": {
        "provider": "ollama",
        "base_url": "http://localhost:11434",
        "model": "qwen2",
        "temperature": 0.7,
        "max_tokens": 4096
    },
    "embedding": {
        "type": "local",
        "model": "BAAI/bge-small-zh-v1.5"
    }
}
