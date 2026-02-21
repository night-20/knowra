import keyring
from loguru import logger

SERVICE_NAME = "Knowra_API_Keys"

def save_api_key(provider: str, api_key: str) -> bool:
    """加密存储 API Key 到 OS 安全管理器"""
    if not api_key:
        return False
    try:
        keyring.set_password(SERVICE_NAME, provider, api_key)
        return True
    except Exception as e:
        logger.error(f"保存 {provider} 的 API Key 失败: {e}")
        return False

def get_api_key(provider: str) -> str | None:
    """从 OS 安全管理器获取 API Key"""
    try:
        return keyring.get_password(SERVICE_NAME, provider)
    except Exception as e:
        logger.error(f"获取 {provider} 的 API Key 失败: {e}")
        return None

def delete_api_key(provider: str) -> bool:
    """从管理器删除 API Key"""
    try:
        keyring.delete_password(SERVICE_NAME, provider)
        return True
    except keyring.errors.PasswordDeleteError:
        return True  # 本来就不存在
    except Exception as e:
        logger.error(f"删除 {provider} 的 API Key 失败: {e}")
        return False
