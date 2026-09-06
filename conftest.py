import os
import pytest
import requests
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv
import uuid
from playwright.sync_api import Page, expect, Browser

os.environ['TESTING_MODE'] = 'true'

load_dotenv()
# --- Конфигурация ---
BASE_URL = os.getenv("APP_URL", "http://127.0.0.1:5000")
TEST_USERNAME = os.getenv("TEST_USERNAME", "admin")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "admin")
AUTH_STATE_PATH = "auth.json"


# --- ФИКСТУРЫ ДЛЯ АВТОРИЗАЦИИ ---

@pytest.fixture(scope="session")
def auth_state(browser: Browser):
    """
    Выполняет логин ОДИН раз на всю сессию тестов
    и сохраняет куки/токены в файл auth.json
    """
    context = browser.new_context()
    page = context.new_page()
    
    page.goto(f"{BASE_URL}/login")
    page.locator("[data-testid='username-input']").fill(TEST_USERNAME)
    page.locator("[data-testid='password-input']").fill(TEST_PASSWORD)
    page.locator("[data-testid='submit-btn']").click()
    
    # Проверяем, что авторизация прошла успешно
    expect(page.locator("[data-testid='files-list-container']")).to_be_visible(timeout=15000)
    
    # Сохраняем состояние авторизации
    context.storage_state(path=AUTH_STATE_PATH)
    context.close()
    
    yield AUTH_STATE_PATH


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args, auth_state):
    """
    Автоматически загружает сохранённое состояние во ВСЕ браузерные контексты.
    Теперь каждая новая страница уже авторизована.
    """
    return {
        **browser_context_args,
        "storage_state": auth_state,
    }


@pytest.fixture(scope="function")
def authenticated_page(page: Page):
    """
    Возвращает уже авторизованную страницу.
    Никаких повторных логинов!
    """
    # Страница уже имеет куки благодаря browser_context_args,
    # просто переходим на главную
    page.goto(f"{BASE_URL}")
    expect(page.locator("[data-testid='files-list-container']")).to_be_visible(timeout=10000)
    yield page


@pytest.fixture(scope="function")
def login_page(page: Page):
    """
    Открывает страницу логина, но НЕ авторизует.
    Для тестов ошибки входа, проверки UI и т.д.
    """
    page.goto(f"{BASE_URL}/login")
    expect(page.locator("[data-testid='auth-form']")).to_be_visible(timeout=10000)
    yield page
@pytest.fixture
def temp_file(tmp_path):
    """Создаёт временный файл для загрузки"""
    file = tmp_path / "test_upload.txt"
    file.write_text("Hello from Playwright test!")
    return file


@pytest.fixture
def temp_img(tmp_path):
    """Создаёт временную картинку для загрузки"""
    file = tmp_path / "test_upload.png"
    img = Image.new('RGB', (100, 100), color='red')
    img.save(str(file), 'PNG')
    return file


@pytest.fixture
def temp_video():
    """Использует готовое видео из test_data/"""
    test_data_dir = Path(__file__).parent / "test_data"
    video_file = test_data_dir / "sample_video.mp4"
    
    if not video_file.exists():
        pytest.skip(f"Файл {video_file} не найден")
    
    return video_file


@pytest.fixture
def multiple_files(tmp_path):
    """Создаёт несколько временных файлов"""
    files = []
    for i in range(3):
        file = tmp_path / f"test_file_{i}.txt"
        file.write_text(f"Content of file {i}")
        files.append(file)
    return files


@pytest.fixture
def large_file(tmp_path):
    """Создаёт большой файл для теста отмены загрузки"""
    file = tmp_path / "large_file.bin"
    # 50 МБ — достаточно большой, чтобы успеть нажать отмену
    file.write_bytes(b"0" * (50 * 1024 * 1024))
    return file


@pytest.fixture(scope="function")
def cleanup_uploaded_files(authenticated_page: Page):
    """
    Автоматически удаляет файлы И папки, загруженные во время теста.
    """
    page = authenticated_page
    
    # 1. Собираем short_id файлов, которые УЖЕ были на странице до теста
    existing_file_ids = set(page.evaluate("""
        () => Array.from(document.querySelectorAll('.file-card[data-short-id]'))
                   .map(el => el.getAttribute('data-short-id'))
    """))
    
    # 2. Собираем пути папок, которые УЖЕ были на странице до теста
    existing_folder_paths = set(page.evaluate("""
        () => Array.from(document.querySelectorAll('.file-card[data-folder-path]'))
                   .map(el => el.getAttribute('data-folder-path'))
    """))
    
    yield  # <-- Здесь выполняется тест
    
    # 3. После теста собираем все short_id файлов
    current_file_ids = set(page.evaluate("""
        () => Array.from(document.querySelectorAll('.file-card[data-short-id]'))
                   .map(el => el.getAttribute('data-short-id'))
    """))
    
    # 4. После теста собираем все пути папок
    current_folder_paths = set(page.evaluate("""
        () => Array.from(document.querySelectorAll('.file-card[data-folder-path]'))
                   .map(el => el.getAttribute('data-folder-path'))
    """))
    
    # 5. Находим новые файлы и папки
    new_file_ids = current_file_ids - existing_file_ids
    new_folder_paths = current_folder_paths - existing_folder_paths
    
    if not new_file_ids and not new_folder_paths:
        print("\n [CLEANUP] Новых файлов и папок не обнаружено, очистка не требуется")
        return
    
    # 6. Получаем CSRF-токен
    csrf_token = page.evaluate("""
        () => {
            const meta = document.querySelector('meta[name="csrf-token"]');
            return meta ? meta.content : null;
        }
    """)
    
    if not csrf_token:
        cookies = page.context.cookies()
        csrf_cookie = next((c for c in cookies if c['name'] == 'csrf_token'), None)
        if csrf_cookie:
            csrf_token = csrf_cookie['value']
    
    headers = {"Content-Type": "application/json"}
    if csrf_token:
        headers["X-CSRFToken"] = csrf_token
        print(f"  🔑 CSRF-токен найден: {csrf_token[:20]}...")
    else:
        print("  ⚠️ CSRF-токен не найден, пробуем без него")
    
    # 7. Удаляем новые файлы
    if new_file_ids:
        print(f"\n🧹 [CLEANUP] Удаляю {len(new_file_ids)} тестовых файлов: {new_file_ids}")
        for short_id in new_file_ids:
            try:
                response = page.request.delete(
                    f"{BASE_URL}/api/delete/{short_id}",
                    headers=headers
                )
                if response.ok:
                    print(f"  ✅ Удалён файл {short_id}")
                else:
                    print(f"  ️ Ошибка удаления файла {short_id}: HTTP {response.status}")
                    try:
                        error_body = response.json()
                        print(f"     Тело ответа: {error_body}")
                    except:
                        print(f"     Тело ответа: {response.text()}")
            except Exception as e:
                print(f"  ❌ Не удалось удалить файл {short_id}: {e}")
    
    # 8. Удаляем новые папки
    if new_folder_paths:
        print(f"\n🧹 [CLEANUP] Удаляю {len(new_folder_paths)} тестовых папок: {new_folder_paths}")
        for folder_path in new_folder_paths:
            try:
                response = page.request.post(
                    f"{BASE_URL}/api/delete/bulk",
                    headers=headers,
                    data={"folder_path": folder_path}
                )
                if response.ok:
                    print(f"  ✅ Удалена папка {folder_path}")
                else:
                    print(f"  ️ Ошибка удаления папки {folder_path}: HTTP {response.status}")
                    try:
                        error_body = response.json()
                        print(f"     Тело ответа: {error_body}")
                    except:
                        print(f"     Тело ответа: {response.text()}")
            except Exception as e:
                print(f"  ❌ Не удалось удалить папку {folder_path}: {e}")

@pytest.fixture(scope="function")
def test_users():
    """
    Создает двух уникальных тестовых пользователей перед тестом.
    Автоматически обрабатывает CSRF-токены.
    """
    import re
    base_url = os.getenv("APP_URL", "http://localhost:5000")
    
    # Генерируем уникальные имена, чтобы тесты не конфликтовали
    user_a_name = f"test_alice_{uuid.uuid4().hex[:8]}"
    user_b_name = f"test_bob_{uuid.uuid4().hex[:8]}"
    password = "TestPassword123!"
    
    users = {
        "user_a": {"username": user_a_name, "password": password},
        "user_b": {"username": user_b_name, "password": password}
    }
    
    # Используем Session для сохранения куки между запросами
    session = requests.Session()
    
    for user_key, user_data in users.items():
        # 1. GET /login — получаем страницу с CSRF-токеном
        get_response = session.get(f"{base_url}/login")
        assert get_response.status_code == 200, f"Не удалось загрузить страницу логина: {get_response.status_code}"
        
        # 2. Извлекаем CSRF-токен из HTML
        # Flask-WTF обычно вставляет его как <input type="hidden" name="csrf_token" value="...">
        match = re.search(
            r'name="csrf_token"\s+value="([^"]+)"', 
            get_response.text
        )
        if not match:
            # Альтернативный вариант: токены иногда бывают в meta-тегах
            match = re.search(
                r'name="csrf-token"\s+content="([^"]+)"',
                get_response.text
            )
        
        assert match, "Не удалось найти CSRF-токен на странице логина. Проверьте HTML-код."
        csrf_token = match.group(1)
        
        # 3. POST /login с CSRF-токеном и флагом регистрации
        post_response = session.post(
            f"{base_url}/login",
            data={
                "csrf_token": csrf_token,
                "username": user_data["username"],
                "password": user_data["password"],
                "register": "1"
            },
            allow_redirects=False  # Не переходим на главную, остаёмся на логине
        )
        
        # 302 = успешная регистрация и редирект на главную
        if post_response.status_code not in [200, 302]:
            pytest.fail(
                f"Не удалось зарегистрировать {user_key}: "
                f"{post_response.status_code} - {post_response.text[:500]}"
            )
        
        # Если пользователь уже существует (302 тоже может быть, но на login с ошибкой),
        # проверяем, что мы не остались на странице с ошибкой
        if post_response.status_code == 200 and "уже существует" in post_response.text:
            # Пользователь уже есть — это нормально, продолжаем
            pass
    
    yield users
