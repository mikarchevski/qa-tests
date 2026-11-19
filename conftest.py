import pytest
from playwright.sync_api import Page, expect
from Pages.login_page import LoginPage
import pytest
import sqlite3
import uuid
import os
from datetime import datetime
from pathlib import Path
from PIL import Image
import imageio.v3 as iio
import numpy as np
from moviepy.editor import ColorClip

from Pages.upload_page import UploadPage
from config import Config


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """
    Глобально добавляет заголовок X-E2E-Bypass-Token ко всем запросам браузера.
    Бэкенд видит этот токен и полностью отключает rate limiting для этих запросов.
    """
    args = dict(browser_context_args)
    args["accept_downloads"] = True  # поддержка скачивания файлов
    # Берем токен из окружения (или из Config.E2E_BYPASS_TOKEN)
    bypass_token = os.getenv("E2E_BYPASS_TOKEN", "my_super_secret_local_token_123")

    # Добавляем заголовок к существующим
    extra_headers = args.get("extra_http_headers", {})
    extra_headers["X-E2E-Bypass-Token"] = bypass_token
    args["extra_http_headers"] = extra_headers

    return args


# фикстура залогиненной страницы
@pytest.fixture
def authenticated_page(login_page: LoginPage):
    login_page.fill_login(Config.TEST_USERNAME, Config.TEST_PASSWORD)
    login_page.send_login_form()
    expect(login_page.page).to_have_url(Config.BASE_URL + "/")
    return login_page.page


@pytest.fixture
def login_page(page: Page) -> LoginPage:
    """
    Фикстура: создает объект LoginPage и открывает страницу логина.
    Используется во всех тестах, где нужен вход на сайт.
    """
    lp = LoginPage(page)
    lp.goto()
    return lp


# фикстура страницы загрузки
@pytest.fixture
def upload_page(authenticated_page) -> UploadPage:
    return UploadPage(authenticated_page)


@pytest.fixture
def valid_invite_code():
    """
    Фикстура: создает валидный инвайт-код в БД для тестов
    """
    code = f"TEST_{uuid.uuid4().hex[:8].upper()}"
    created_at = datetime.now().isoformat()

    # Подключаемся к БД
    conn = sqlite3.connect(Config.DB_PATH)
    cursor = conn.cursor()

    try:
        # Это позволяет вставить код, не создавая предварительно запись в admin_users.
        cursor.execute("PRAGMA foreign_keys = OFF")

        # Вставляем инвайт-код. created_by=1 (условный админ), is_active=1 (активен)
        cursor.execute('''
                       INSERT INTO invite_codes (code, created_by, created_at, is_active)
                       VALUES (?, ?, ?, ?)
                       ''', (code, 1, created_at, 1))
        conn.commit()

        # Отдаем сгенерированный код прямо в тест
        yield code

    finally:
        conn.close()


# фикстура создания одного временного файла
@pytest.fixture
def temp_file(tmp_path):
    file_path = tmp_path / "test_automation_file.txt"
    file_path.write_text("Hello World")
    yield file_path.absolute()


@pytest.fixture
def temp_files(tmp_path):
    """
    Фикстура: создает N временных файлов и возвращает список путей.
    """
    file_names = ["test_image.png", "test_document.txt", "test_data.csv"]
    paths = []

    for name in file_names:
        file_path = tmp_path / name
        file_path.write_text(f"Контент файла {name}")
        paths.append(file_path.absolute())

    yield paths
    # Очистка не нужна — tmp_path удалит всё сам


@pytest.fixture
def temp_folder(tmp_path):
    test_folder = tmp_path / "test_folder"
    test_folder.mkdir()
    (test_folder / "test_file.txt").write_text("Hello World")
    (test_folder / "test_document.txt").write_text("Hello World")
    yield test_folder


@pytest.fixture(scope="function")
def cleanup_uploaded_files(authenticated_page: Page, api_auth_headers: dict):
    """
    Автоматически удаляет ТОЛЬКО те файлы и папки, которые были загружены во время теста.
    Использует дельта-подход для максимальной безопасности и скорости.
    """
    page = authenticated_page

    # 1. Собираем short_id файлов, которые УЖЕ были на странице ДО теста
    existing_file_ids = set(page.evaluate("""
                                          () => Array.from(document.querySelectorAll('.file-card[data-short-id]'))
                                              .map(el => el.getAttribute('data-short-id'))
                                          """))

    # 2. Собираем пути папок, которые УЖЕ были на странице ДО теста
    existing_folder_paths = set(page.evaluate("""
                                              () => Array.from(document.querySelectorAll('.file-card[data-folder-path]'))
                                                  .map(el => el.getAttribute('data-folder-path'))
                                              """))

    # 🔥 Здесь выполняется сам тест
    yield

    # 3-5. (Код сбора new_file_ids и new_folder_paths остаётся без изменений)
    current_file_ids = set(page.evaluate("""
                                         () => Array.from(document.querySelectorAll('.file-card[data-short-id]'))
                                             .map(el => el.getAttribute('data-short-id'))
                                         """))
    current_folder_paths = set(page.evaluate("""
                                             () => Array.from(document.querySelectorAll('.file-card[data-folder-path]'))
                                                 .map(el => el.getAttribute('data-folder-path'))
                                             """))
    new_file_ids = current_file_ids - existing_file_ids
    new_folder_paths = current_folder_paths - existing_folder_paths

    if not new_file_ids and not new_folder_paths:
        print("\n✨ [CLEANUP] Новых файлов и папок не обнаружено, очистка не требуется")
        return

    # 6. 🔥 ИСПОЛЬЗУЕМ ГОТОВУЮ ФИКСТУРУ ВМЕСТО ДУБЛИРОВАНИЯ
    headers = {"Content-Type": "application/json"}
    headers.update(api_auth_headers)  # Добавляем CSRF-токен из фикстуры

    print(f"\n🔑 [CLEANUP] CSRF-токен добавлен из фикстуры")


@pytest.fixture(scope="function")
def api_cleanup_files(authenticated_page: Page, api_auth_headers):
    """
    Автоматически удаляет файлы, созданные во время API-теста.
    Работает на уровне бэкенда, не завися от UI/DOM.
    """
    # 1. Запоминаем ID файлов ДО теста
    response_before = authenticated_page.request.get(
        f"{Config.BASE_URL}/api/files?per_page=100",
        headers=api_auth_headers
    )
    ids_before = {f["short_id"] for f in response_before.json().get("files", [])}

    yield

    # 2. Запоминаем ID файлов ПОСЛЕ теста
    response_after = authenticated_page.request.get(
        f"{Config.BASE_URL}/api/files?per_page=100",
        headers=api_auth_headers
    )
    ids_after = {f["short_id"] for f in response_after.json().get("files", [])}

    # 3. Находим новые файлы (дельта)
    new_file_ids = list(ids_after - ids_before)

    if not new_file_ids:
        return  # Нечего удалять

    # 4. Удаляем их через массовое удаление (bulk delete)
    delete_resp = authenticated_page.request.post(
        f"{Config.BASE_URL}/api/delete/bulk",
        headers=api_auth_headers,
        data={"short_ids": new_file_ids}
    )

    # Можно добавить проверку, чтобы убедиться, что очистка прошла успешно
    if not delete_resp.ok:
        print(f"⚠️ [CLEANUP] Не удалось удалить тестовые файлы: {delete_resp.text()}")

#Создание временной картинки
@pytest.fixture
def test_image(tmp_path: Path):
    img = Image.new('RGB', (100,100), color='red')
    import_path = tmp_path / 'image.png'
    img.save(import_path)
    yield import_path

#Создание видео
@pytest.fixture
def test_video(tmp_path: Path) -> Path:
    """
    Фикстура: создает тестовое видео MP4 длительностью 1 секунда.
    Видео — красный квадрат 100x100 пикселей.
    """
    video_path = tmp_path / "test_video.mp4"
    
    # Создаем красное видео 100x100 пикселей, длительностью 1 секунда
    clip = ColorClip(size=(100, 100), color=(255, 0, 0), duration=1)
    
    # Записываем в файл (без звука, без логов)
    clip.write_videofile(
        str(video_path),
        fps=30,
        codec='libx264',
        audio=False,
        logger=None
    )
    
    clip.close()
    
    yield video_path

@pytest.fixture
def api_request(authenticated_page: Page):
    """
    Возвращает объект Playwright Request с уже авторизованным контекстом.
    Позволяет делать API-запросы так, как будто их делает залогиненный пользователь.
    """
    return authenticated_page.request


@pytest.fixture
def api_auth_headers(authenticated_page: Page) -> dict:
    """
    Возвращает словарь заголовков с CSRF-токеном для API-запросов.
    Автоматически извлекает токен из кук авторизованной сессии.
    """
    cookies = authenticated_page.context.cookies()
    csrf_cookie = next((c for c in cookies if c["name"] == "csrf_token"), None)

    headers = {}
    if csrf_cookie:
        headers["X-CSRFToken"] = csrf_cookie["value"]

    return headers