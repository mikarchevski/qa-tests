import os
from pathlib import Path
from dotenv import load_dotenv
import time

# Находим корень проекта (папку, где лежит этот файл)
BASE_DIR = Path(__file__).resolve().parent

# Загружаем переменные из .env
load_dotenv(BASE_DIR / ".env")

E2E_BYPASS_TOKEN: str = os.getenv("E2E_BYPASS_TOKEN", "")


class Config:
    """Централизованное хранилище всех настроек проекта"""

    # Учетные данные
    TEST_USERNAME: str = os.getenv("TEST_USERNAME", "default_user")
    TEST_PASSWORD: str = os.getenv("TEST_PASSWORD", "default_password")

    # URL стенда
    BASE_URL: str = os.getenv("BASE_URL", "http://127.0.0.1:5000")

    # Токены
    E2E_BYPASS_TOKEN: str = os.getenv("E2E_BYPASS_TOKEN", "")

    INVALID_PASSWORD: str = os.getenv("INVALID_PASSWORD", "wrong_pass")

    # Данные для регистрации
    REG_USERNAME: str = os.getenv("REG_USERNAME", "testuser")
    REG_PASSWORD: str = os.getenv("REG_PASSWORD", "111111")
    REG_INVITE_CODE: str = os.getenv("REG_INVITE_CODE", "testcode")
    DB_PATH: str = os.getenv("DB_PATH", str(BASE_DIR / "data" / "uploads.db"))

    @staticmethod
    def unique_username() -> str:
        """Генерирует уникальный username для каждого прогона"""
        return f"{Config.REG_USERNAME}_{int(time.time())}"
