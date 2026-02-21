import sys
import os
from pathlib import Path

# 将项目根目录放入环境变量方便 import
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.app import KnowraApp

def main():
    app = KnowraApp(sys.argv)
    sys.exit(app.run())

if __name__ == "__main__":
    main()
