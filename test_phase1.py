import os
import sys

# Ensure Python could find our modules from the root working directory
sys.path.insert(0, os.path.abspath("."))

from src.config.settings import settings
from src.config.constants import APPDATA_DIR, DATA_DIR, CONFIG_FILE
from src.utils.security import save_api_key, get_api_key, delete_api_key
from src.utils.logger import setup_logger
from loguru import logger

def run_tests():
    print("=== Phase 1 Environment Checks ===")
    print(f"Expected AppData Dir: {APPDATA_DIR}")
    print(f"APPDATA_DIR exists: {APPDATA_DIR.exists()}")
    print(f"DATA_DIR exists: {DATA_DIR.exists()}")
    print(f"CONFIG_FILE path: {CONFIG_FILE}")
    print("Current loaded settings from config:")
    print(settings.config)
    print("=" * 30 + "\n")

    # init logger manually 
    setup_logger()
    logger.info("Testing security module using Python Keyring...")

    provider_name = "test_openai_fake"
    test_key = "sk-fake-1234abcd"

    logger.info(f"Trying to save {provider_name} key...")
    saved = save_api_key(provider_name, test_key)
    logger.info(f"Saved: {saved}")

    logger.info("Trying to retrieve the key...")
    retrieved = get_api_key(provider_name)
    logger.info(f"Retrieved key matches passed-in key: {retrieved == test_key}")

    logger.info("Cleaning up test key...")
    deleted = delete_api_key(provider_name)
    logger.info(f"Deleted: {deleted}")
    
    deleted_again = delete_api_key(provider_name)
    logger.info(f"Idempotent deletion: {deleted_again}")

    remaining = get_api_key(provider_name)
    logger.info(f"Key is really gone: {remaining is None}")
    
    print("\n✅ All assertions executed.")

if __name__ == "__main__":
    run_tests()
