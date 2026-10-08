import pytest
from playwright.sync_api import Page, expect
from Pages.login_page import LoginPage
import pytest
import sqlite3
import uuid
import os
from datetime import datetime
from pathlib import Path

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
def cleanup_uploaded_files(authenticated_page: Page):
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

    # 3. После теста собираем текущие short_id файлов
    current_file_ids = set(page.evaluate("""
                                         () => Array.from(document.querySelectorAll('.file-card[data-short-id]'))
                                             .map(el => el.getAttribute('data-short-id'))
                                         """))

    # 4. После теста собираем текущие пути папок
    current_folder_paths = set(page.evaluate("""
                                             () => Array.from(document.querySelectorAll('.file-card[data-folder-path]'))
                                                 .map(el => el.getAttribute('data-folder-path'))
                                             """))

    # 5. Находим НОВЫЕ файлы и папки (разница множеств)
    new_file_ids = current_file_ids - existing_file_ids
    new_folder_paths = current_folder_paths - existing_folder_paths

    if not new_file_ids and not new_folder_paths:
        print("\n✨ [CLEANUP] Новых файлов и папок не обнаружено, очистка не требуется")
        return

    # 6. Получаем CSRF-токен (из meta-тега или куки)
    csrf_token = page.evaluate("""
                               () => {
                                   const meta = document.querySelector('meta[name="csrf-token"]');
                                   return meta ? meta.content : null;
                               }
                               """)

    if not csrf_token:
        cookies = page.context.cookies()
        csrf_cookie = next((c for c in cookies if c['name'] in ['csrf_token', 'csrftoken', '_csrf_token']), None)
        if csrf_cookie:
            csrf_token = csrf_cookie['value']

    headers = {"Content-Type": "application/json"}
    if csrf_token:
        headers["X-CSRFToken"] = csrf_token
        print(f"\n🔑 [CLEANUP] CSRF-токен найден")
    else:
        print("\n⚠️ [CLEANUP] CSRF-токен не найден, пробуем без него")

    # 7. Удаляем новые файлы (через DELETE, как требует бэкенд)
    if new_file_ids:
        print(f"\n🧹 [CLEANUP] Удаляю {len(new_file_ids)} тестовых файлов...")
        for short_id in new_file_ids:
            try:
                response = page.request.delete(
                    f"{Config.BASE_URL}/api/delete/{short_id}",
                    headers=headers
                )
                if response.ok:
                    print(f"  ✅ Удалён файл: {short_id}")
                else:
                    print(f"  ❌ Ошибка удаления файла {short_id}: HTTP {response.status} | {response.text()}")
            except Exception as e:
                print(f"  ❌ Не удалось удалить файл {short_id}: {e}")

    # 8. Удаляем новые папки (через POST bulk, как требует бэкенд)
    if new_folder_paths:
        print(f"\n🧹 [CLEANUP] Удаляю {len(new_folder_paths)} тестовых папок...")
        for folder_path in new_folder_paths:
            try:
                response = page.request.post(
                    f"{Config.BASE_URL}/api/delete/bulk",
                    headers=headers,
                    data={"folder_path": folder_path}  # 🔥 Важно: data, а не json
                )
                if response.ok:
                    print(f"  ✅ Удалена папка: {folder_path}")
                else:
                    print(f"  ❌ Ошибка удаления папки {folder_path}: HTTP {response.status} | {response.text()}")
            except Exception as e:
                print(f"  ❌ Не удалось удалить папку {folder_path}: {e}")
