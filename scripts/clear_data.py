import shutil
import os
from pathlib import Path

appdata_path = Path(os.environ.get('APPDATA', '')) / 'Knowra'
if appdata_path.exists():
    shutil.rmtree(appdata_path, ignore_errors=True)
    print("Cleared Knowra AppData")

tests_path = Path('tests')
if tests_path.exists():
    shutil.rmtree(tests_path, ignore_errors=True)
    print("Cleared tests directory")

test_script = Path('test_phase1.py')
if test_script.exists():
    test_script.unlink(missing_ok=True)
    print("Cleared test_phase1.py")
