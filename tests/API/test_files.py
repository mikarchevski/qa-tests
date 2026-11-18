import pytest
import hashlib
from config import Config
from playwright.sync_api import Page


def test_api_file_lifecycle(authenticated_page: Page, temp_file, api_auth_headers):
    """
    Сценарий: Полный цикл жизни файла через API (Загрузка -> Проверка -> Удаление)
    """
    # 1. ПОДГОТОВКА: Вычисляем хэш файла
    file_hash = hashlib.sha256(temp_file.read_bytes()).hexdigest()

    # 2. ЗАГРУЗКА через API
    with open(temp_file, "rb") as f:
        response = authenticated_page.request.post(
            f"{Config.BASE_URL}/upload",
            headers=api_auth_headers,  # 🔥 Просто передаём готовый словарь
            multipart={
                "file": {
                    "name": temp_file.name,
                    "mimeType": "text/plain",
                    "buffer": f.read()
                },
                "hash": file_hash,
                "folder_path": ""
            }
        )

    assert response.ok, f"Загрузка не удалась: {response.status} - {response.text()}"
    short_id = response.json()["file_data"]["short_id"]

    # 3. ПРОВЕРКА: Файл есть в списке
    list_response = authenticated_page.request.get(
        f"{Config.BASE_URL}/api/files?per_page=20",
        headers=api_auth_headers
    )
    assert list_response.ok
    files_data = list_response.json()["files"]
    assert any(f["short_id"] == short_id for f in files_data), "Файл не найден в API"

    # 4. УДАЛЕНИЕ через API
    delete_response = authenticated_page.request.delete(
        f"{Config.BASE_URL}/api/delete/{short_id}",
        headers=api_auth_headers
    )
    assert delete_response.ok
    assert delete_response.json()["success"] is True

    # 5. ПРОВЕРКА: Файл удалён
    list_response_after = authenticated_page.request.get(
        f"{Config.BASE_URL}/api/files?per_page=20",
        headers=api_auth_headers
    )
    files_after = list_response_after.json()["files"]
    assert not any(f["short_id"] == short_id for f in files_after), "Файл не был удалён!"