import os
from pathlib import Path

from dotenv import dotenv_values


BASE_DIR = Path(__file__).resolve().parents[1]
IS_VERCEL = bool(os.environ.get("VERCEL"))
RUNTIME_DATA_DIR = Path(os.environ.get("JARVIS_DATA_DIR", "/tmp/jarvis-data" if IS_VERCEL else BASE_DIR / "Data"))


def load_env():
    return {**dotenv_values(BASE_DIR / ".env"), **os.environ}


def data_path(*parts):
    RUNTIME_DATA_DIR.mkdir(parents=True, exist_ok=True)
    return RUNTIME_DATA_DIR.joinpath(*parts)


def chat_log_path():
    return data_path("ChatLog.json")


def speech_path():
    return data_path("speech.mp3")
