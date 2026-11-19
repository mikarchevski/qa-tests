import pytest
import hashlib
from config import Config
from playwright.sync_api import Page


def test_api_health_check_main_page(page: Page):
    """Сценарий: Главная страница доступна и отдаёт HTML (Сервер жив)"""
    response = page.request.get(Config.BASE_URL)

    assert response.status == 200, "Главная страница недоступна"
    # Проверяем, что это именно HTML, а не ошибка в формате JSON или plain text
    assert "text/html" in response.headers.get("content-type", "")


def test_api_delete_non_existent_file(authenticated_page: Page, api_auth_headers):
    """Сценарий: Удаление несуществующего файла возвращает 404, а не 500"""
    fake_short_id = "fake_id_that_does_not_exist_123"

    response = authenticated_page.request.delete(
        f"{Config.BASE_URL}/api/delete/{fake_short_id}",
        headers=api_auth_headers
    )

    assert response.status == 404
    response_data = response.json()
    assert response_data["error"] is True
    assert response_data["message"] == "File not found"

def test_api_file_lifecycle(authenticated_page: Page, temp_file, api_cleanup_files, api_auth_headers):
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


def test_api_upload_without_csrf_fails(authenticated_page: Page, temp_file, api_cleanup_files):
    """Сценарий: Попытка загрузить файл без CSRF-токена должна быть отклонена"""
    file_hash = hashlib.sha256(temp_file.read_bytes()).hexdigest()

    with open(temp_file, "rb") as f:
        # Намеренно НЕ передаем api_auth_headers
        response = authenticated_page.request.post(
            f"{Config.BASE_URL}/upload",
            multipart={
                "file": {"name": temp_file.name, "mimeType": "text/plain", "buffer": f.read()},
                "hash": file_hash,
                "folder_path": ""
            }
        )

    assert response.status == 400
    assert "CSRF token is missing" in response.text()


def test_api_files_requires_auth(page: Page):
    """Сценарий: Запрос списка файлов без авторизации возвращает 401"""
    # Используем чистый page.request без фикстуры authenticated_page
    response = page.request.get(f"{Config.BASE_URL}/api/files")
    assert response.status == 401
    response_data = response.json()
    assert response_data["error"] is True
    assert response_data["message"] == "Требуется авторизация"


def test_api_download_file_integrity(authenticated_page: Page, temp_file, api_cleanup_files, api_auth_headers):
    """Сценарий: Скачанный через API файл идентичен оригиналу"""

    # 1. Загружаем файл
    file_hash = hashlib.sha256(temp_file.read_bytes()).hexdigest()

    with open(temp_file, "rb") as f:
        upload_resp = authenticated_page.request.post(
            f"{Config.BASE_URL}/upload",
            headers=api_auth_headers,
            multipart={
                "file": {
                    "name": temp_file.name,
                    "mimeType": "text/plain",  # 🔥 Важно оставить mimeType
                    "buffer": f.read()
                },
                "hash": file_hash,
                "folder_path": ""
            }
        )
    assert upload_resp.ok, f"Загрузка не удалась: HTTP {upload_resp.status} | {upload_resp.text()}"

    short_id = upload_resp.json()["file_data"]["short_id"]

    # 2. Скачиваем файл через эндпоинт /d/<short_id>
    download_resp = authenticated_page.request.get(
        f"{Config.BASE_URL}/d/{short_id}",
        headers=api_auth_headers
    )

    assert download_resp.ok, f"Скачивание не удалось: HTTP {download_resp.status} | {download_resp.text()}"

    # 3. Сравниваем хэш скачанного содержимого с оригиналом
    # download_resp.body() возвращает байты скачанного файла
    downloaded_hash = hashlib.sha256(download_resp.body()).hexdigest()

    assert downloaded_hash == file_hash, "Хэш скачанного файла не совпадает с оригиналом!"


def test_api_check_file_exists(authenticated_page: Page, temp_file, api_auth_headers, api_cleanup_files):
    """Сценарий: Эндпоинт /check корректно определяет наличие файла по хэшу"""

    # Делаем содержимое уникальным, чтобы избежать коллизий хэшей
    import uuid
    unique_content = f"Hello World {uuid.uuid4()}"
    temp_file.write_text(unique_content)

    file_hash = hashlib.sha256(temp_file.read_bytes()).hexdigest()

    # 1. До загрузки файла его не существует
    check_before = authenticated_page.request.get(
        f"{Config.BASE_URL}/check?hash={file_hash}",
        headers=api_auth_headers
    )
    assert check_before.ok
    assert check_before.json()["exists"] is False

    # 2. Загружаем файл
    with open(temp_file, "rb") as f:
        upload_resp = authenticated_page.request.post(
            f"{Config.BASE_URL}/upload",
            headers=api_auth_headers,
            multipart={
                "file": {"name": temp_file.name, "mimeType": "text/plain", "buffer": f.read()},
                "hash": file_hash,
                "folder_path": ""
            }
        )
    assert upload_resp.ok

    # 3. Теперь эндпоинт должен сказать, что файл существует
    check_after = authenticated_page.request.get(
        f"{Config.BASE_URL}/check?hash={file_hash}",
        headers=api_auth_headers
    )
    assert check_after.ok
    assert check_after.json()["exists"] is True
    assert check_after.json()["owned"] is True
