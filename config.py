"""Project configuration loaded from environment and the local .env file."""

import os
from pathlib import Path
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"


load_dotenv(dotenv_path=str(ENV_FILE), override=False)


def _as_bool(value):
    return str(value).strip().lower() in ("1", "true", "yes", "on")


class Config(object):
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.environ.get("APP_SECRET_KEY", "local-development-key-change-before-deploy")
    DEBUG = _as_bool(os.environ.get("FLASK_DEBUG", "0"))
    HOST = os.environ.get("FLASK_HOST", "127.0.0.1")
    PORT = int(os.environ.get("FLASK_PORT", "5000"))
    DATABASE_PATH = os.environ.get("BUS_DATABASE_PATH") or str(BASE_DIR / "bus_project.db")

