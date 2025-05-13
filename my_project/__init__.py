# my_project/__init__.py

import os
from pathlib import Path

def ensure_log_file_exists():
    logs_dir = Path(__file__).resolve().parent.parent / "logs"
    log_file = logs_dir / "transactions.log"

    if not logs_dir.exists():
        logs_dir.mkdir(parents=True)
    
    if not log_file.exists():
        log_file.touch()

ensure_log_file_exists()
