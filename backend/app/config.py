import os
from pathlib import Path


class Settings:
    APP_TITLE = "Dự Toán Web"
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / "data"

    # Allow overriding the database path via environment variable
    # (used by the packaged Electron app)
    _db_override = os.environ.get("DUTOAN_DB_PATH")
    if _db_override:
        DATABASE_URL = f"sqlite:///{_db_override}"
    else:
        DATABASE_URL = f"sqlite:///{DATA_DIR / 'dutoan.db'}"

    MDB_DATA_DIR = Path(os.environ.get(
        "DUTOAN_MDB_DIR",
        r"C:\Users\minhk\Downloads\Dulieu",
    ))


settings = Settings()
