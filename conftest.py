# -*- coding: utf-8 -*-
import os
import pytest
import allure
from dotenv import load_dotenv
from playwright.sync_api import Page
from fixtures.upload import *  # noqa
load_dotenv()
# Читаем из переменных окружения, иначе используем дефолтные значения
BASE_URL = os.getenv("APP_URL", "http://127.0.0.1:5000")
TEST_USERNAME = os.getenv("TEST_USERNAME", "test_user_qa")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "TestPassword123!")


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


@pytest.fixture(scope="function")
def cleanup_uploaded_files(authenticated_page: Page):
    """
    Автоматически удаляет файлы, загруженные во время теста.
    """
    page = authenticated_page
    
    # 1. Собираем short_id файлов, которые УЖЕ были на странице до теста
    existing_ids = set(page.evaluate("""
        () => Array.from(document.querySelectorAll('.file-card[data-short-id]'))
                   .map(el => el.getAttribute('data-short-id'))
    """))
    
    yield  # <-- Здесь выполняется тест
    
    # 2. После теста собираем все short_id, которые есть сейчас
    current_ids = set(page.evaluate("""
        () => Array.from(document.querySelectorAll('.file-card[data-short-id]'))
                   .map(el => el.getAttribute('data-short-id'))
    """))
    
    # 3. Находим новые файлы (те, которых не было до теста)
    new_ids = current_ids - existing_ids
    
    if new_ids:
        print(f"\n🧹 [CLEANUP] Удаляю {len(new_ids)} тестовых файлов: {new_ids}")
        
        # Получаем CSRF-токен из мета-тега страницы
        csrf_token = page.evaluate("""
            () => {
                const meta = document.querySelector('meta[name="csrf-token"]');
                return meta ? meta.content : null;
            }
        """)
        
        # Если в мета-теге нет, пробуем получить из кук
        if not csrf_token:
            cookies = page.context.cookies()
            csrf_cookie = next((c for c in cookies if c['name'] == 'csrf_token'), None)
            if csrf_cookie:
                csrf_token = csrf_cookie['value']
        
        # Формируем заголовки
        headers = {"Content-Type": "application/json"}
        if csrf_token:
            headers["X-CSRFToken"] = csrf_token
            print(f"  🔑 CSRF-токен найден: {csrf_token[:20]}...")
        else:
            print("  ⚠️ CSRF-токен не найден, пробуем без него")
        
        for short_id in new_ids:
            try:
                response = page.request.delete(
                    f"{BASE_URL}/api/delete/{short_id}",
                    headers=headers
                )
                if response.ok:
                    print(f"  ✅ Удалён {short_id}")
                else:
                    print(f"  ⚠️ Ошибка удаления {short_id}: HTTP {response.status}")
                    # Выводим тело ответа для диагностики
                    try:
                        error_body = response.json()
                        print(f"     Тело ответа: {error_body}")
                    except:
                        print(f"     Тело ответа: {response.text()}")
            except Exception as e:
                print(f"  ❌ Не удалось удалить {short_id}: {e}")
    else:
        print("\n🧹 [CLEANUP] Новых файлов не обнаружено, очистка не требуется")