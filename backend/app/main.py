from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.config import settings
from sqlalchemy import inspect, text

from app.database import Base, engine
import app.models.project  # noqa: F401 — register project tables
import app.models.user  # noqa: F401 — register user tables


def _run_migrations():
    """Add columns/tables that create_all cannot add to existing tables."""
    insp = inspect(engine)

    # Add bid_package_id to project_items if missing
    if "project_items" in insp.get_table_names():
        columns = [c["name"] for c in insp.get_columns("project_items")]
        if "bid_package_id" not in columns:
            with engine.begin() as conn:
                conn.execute(text(
                    "ALTER TABLE project_items ADD COLUMN bid_package_id INTEGER "
                    "REFERENCES bid_packages(id) ON DELETE SET NULL"
                ))

    # Add estimate_type to projects if missing
    if "projects" in insp.get_table_names():
        columns = [c["name"] for c in insp.get_columns("projects")]
        if "estimate_type" not in columns:
            with engine.begin() as conn:
                conn.execute(text(
                    "ALTER TABLE projects ADD COLUMN estimate_type VARCHAR(20) DEFAULT 'new'"
                ))

    # Add K coefficients to project_settings if missing
    if "project_settings" in insp.get_table_names():
        columns = [c["name"] for c in insp.get_columns("project_settings")]
        with engine.begin() as conn:
            if "k_vlc" not in columns:
                conn.execute(text("ALTER TABLE project_settings ADD COLUMN k_vlc FLOAT"))
            if "k_nc" not in columns:
                conn.execute(text("ALTER TABLE project_settings ADD COLUMN k_nc FLOAT"))
            if "k_mtc" not in columns:
                conn.execute(text("ALTER TABLE project_settings ADD COLUMN k_mtc FLOAT"))

    # Add settlement columns to project_items if missing
    if "project_items" in insp.get_table_names():
        columns = [c["name"] for c in insp.get_columns("project_items")]
        if "actual_quantity" not in columns:
            with engine.begin() as conn:
                conn.execute(text(
                    "ALTER TABLE project_items ADD COLUMN actual_quantity REAL"
                ))
        if "acceptance_date" not in columns:
            with engine.begin() as conn:
                conn.execute(text(
                    "ALTER TABLE project_items ADD COLUMN acceptance_date DATETIME"
                ))
        if "acceptance_notes" not in columns:
            with engine.begin() as conn:
                conn.execute(text(
                    "ALTER TABLE project_items ADD COLUMN acceptance_notes TEXT"
                ))

    # Add metadata columns to project_settings if missing
    if "project_settings" in insp.get_table_names():
        columns = [c["name"] for c in insp.get_columns("project_settings")]
        if "chu_dau_tu" not in columns:
            with engine.begin() as conn:
                conn.execute(text(
                    "ALTER TABLE project_settings ADD COLUMN chu_dau_tu VARCHAR(255)"
                ))
        if "dia_diem" not in columns:
            with engine.begin() as conn:
                conn.execute(text(
                    "ALTER TABLE project_settings ADD COLUMN dia_diem VARCHAR(255)"
                ))
        if "nguoi_lap" not in columns:
            with engine.begin() as conn:
                conn.execute(text(
                    "ALTER TABLE project_settings ADD COLUMN nguoi_lap VARCHAR(100)"
                ))
        if "nguoi_kiem_tra" not in columns:
            with engine.begin() as conn:
                conn.execute(text(
                    "ALTER TABLE project_settings ADD COLUMN nguoi_kiem_tra VARCHAR(100)"
                ))

    # Add user_id to projects if missing
    if "projects" in insp.get_table_names():
        columns = [c["name"] for c in insp.get_columns("projects")]
        if "user_id" not in columns:
            with engine.begin() as conn:
                conn.execute(text(
                    "ALTER TABLE projects ADD COLUMN user_id INTEGER REFERENCES users(id)"
                ))

    # Create default admin user if users table is empty
    if "users" in insp.get_table_names():
        with engine.begin() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
            if count == 0:
                from app.services.auth_service import hash_password
                hashed = hash_password("admin123")
                conn.execute(text(
                    "INSERT INTO users (username, email, hashed_password, full_name, role, is_active) "
                    "VALUES (:u, :e, :p, :f, :r, 1)"
                ), {"u": "admin", "e": "admin@dutoan.local", "p": hashed, "f": "Administrator", "r": "admin"})


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    _run_migrations()
    yield


app = FastAPI(title=settings.APP_TITLE, version="0.1.0", lifespan=lifespan, debug=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
def root():
    return {"app": settings.APP_TITLE, "version": "0.1.0"}
