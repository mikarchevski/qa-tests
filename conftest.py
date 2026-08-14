# -*- coding: utf-8 -*-
import os
import pytest
import allure
from playwright.sync_api import Page

# Читаем из переменных окружения, иначе используем дефолтные значения
BASE_URL = os.getenv("APP_URL", "https://benx-share.duckdns.org")
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