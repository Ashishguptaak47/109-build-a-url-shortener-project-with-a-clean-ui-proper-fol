import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "urls.db"))
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
