import pytest
import requests
import os
from dotenv import load_dotenv

load_dotenv()
BASE_URL = os.getenv("APP_URL", "http://localhost:5000")

class TestApiSecurity:
    """Проверка базовой безопасности API"""

    def test_api_files_without_auth(self):
        """Попытка получить список файлов без авторизации"""
        response = requests.get(f"{BASE_URL}/api/files")
        
        # Ожидаем 401 Unauthorized или 302 Redirect на страницу логина
        assert response.status_code in [302, 401, 403], \
            f"Ожидался запрет доступа, но получен статус {response.status_code}"

    def test_api_delete_without_auth(self):
        """Попытка удалить файл (с фейковым ID) без авторизации"""
        fake_id = "999999"
        response = requests.delete(f"{BASE_URL}/api/delete/{fake_id}")
        
        assert response.status_code in [302, 400, 401, 403], \
            f"API не защитил эндпоинт удаления! Статус: {response.status_code}"