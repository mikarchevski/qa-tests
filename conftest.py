# -*- coding: utf-8 -*-
import os
import pytest
import allure
import uuid
import requests
from dotenv import load_dotenv
from playwright.sync_api import Page, expect
from fixtures.upload import *  # noqa
load_dotenv()
# Читаем из переменных окружения, иначе используем дефолтные значения
BASE_URL = os.getenv("APP_URL", "http://127.0.0.1:5000")
TEST_USERNAME = os.getenv("TEST_USERNAME", "test_user_qa")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "TestPassword123!")

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

    
@pytest.fixture(scope="function")
def page_with_login(page: Page):
    page.goto(f"{BASE_URL}/login")
    page.get_by_test_id("auth-form").wait_for(state="visible", timeout=10000)
    yield page


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call" and rep.failed:
        page = item.funcargs.get("page") or item.funcargs.get("page_with_login")

        if page:
            screenshot_dir = "screenshots"
            os.makedirs(screenshot_dir, exist_ok=True)

            safe_name = item.name.replace("[", "_").replace("]", "_").replace(":", "_")
            screenshot_path = f"{screenshot_dir}/failed_{safe_name}.png"

            try:
                page.screenshot(path=screenshot_path, full_page=True)

                allure.attach.file(
                    screenshot_path,
                    name="Скриншот ошибки",
                    attachment_type=allure.attachment_type.PNG
                )
                print(f"\n📸 Скриншот ошибки сохранен: {screenshot_path}")
            except Exception as e:
                print(f"\n⚠️ Не удалось сделать скриншот: {e}")


# @pytest.fixture(scope="function")
# def cleanup_uploaded_files(authenticated_page: Page):
#     """
#     Автоматически удаляет файлы, загруженные во время теста.
#     """
#     page = authenticated_page
    
#     # 1. Собираем short_id файлов, которые УЖЕ были на странице до теста
#     existing_ids = set(page.evaluate("""
#         () => Array.from(document.querySelectorAll('.file-card[data-short-id]'))
#                    .map(el => el.getAttribute('data-short-id'))
#     """))
    
#     yield  # <-- Здесь выполняется тест
    
#     # 2. После теста собираем все short_id, которые есть сейчас
#     current_ids = set(page.evaluate("""
#         () => Array.from(document.querySelectorAll('.file-card[data-short-id]'))
#                    .map(el => el.getAttribute('data-short-id'))
#     """))
    
#     # 3. Находим новые файлы (те, которых не было до теста)
#     new_ids = current_ids - existing_ids
    
#     if new_ids:
#         print(f"\n🧹 [CLEANUP] Удаляю {len(new_ids)} тестовых файлов: {new_ids}")
        
#         # Получаем CSRF-токен из мета-тега страницы
#         csrf_token = page.evaluate("""
#             () => {
#                 const meta = document.querySelector('meta[name="csrf-token"]');
#                 return meta ? meta.content : null;
#             }
#         """)
        
#         # Если в мета-теге нет, пробуем получить из кук
#         if not csrf_token:
#             cookies = page.context.cookies()
#             csrf_cookie = next((c for c in cookies if c['name'] == 'csrf_token'), None)
#             if csrf_cookie:
#                 csrf_token = csrf_cookie['value']
        
#         # Формируем заголовки
#         headers = {"Content-Type": "application/json"}
#         if csrf_token:
#             headers["X-CSRFToken"] = csrf_token
#             print(f"  🔑 CSRF-токен найден: {csrf_token[:20]}...")
#         else:
#             print("  ⚠️ CSRF-токен не найден, пробуем без него")
        
#         for short_id in new_ids:
#             try:
#                 response = page.request.delete(
#                     f"{BASE_URL}/api/delete/{short_id}",
#                     headers=headers
#                 )
#                 if response.ok:
#                     print(f"  ✅ Удалён {short_id}")
#                 else:
#                     print(f"  ⚠️ Ошибка удаления {short_id}: HTTP {response.status}")
#                     # Выводим тело ответа для диагностики
#                     try:
#                         error_body = response.json()
#                         print(f"     Тело ответа: {error_body}")
#                     except:
#                         print(f"     Тело ответа: {response.text()}")
#             except Exception as e:
#                 print(f"  ❌ Не удалось удалить {short_id}: {e}")
#     else:
#         print("\n🧹 [CLEANUP] Новых файлов не обнаружено, очистка не требуется")

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