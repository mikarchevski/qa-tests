# -*- coding: utf-8 -*-
import allure
import os
from dotenv import load_dotenv
from playwright.sync_api import Page, expect
from conftest import BASE_URL, TEST_USERNAME, TEST_PASSWORD

# load_dotenv()
# BASE_URL = os.getenv("APP_URL", "http://localhost:5000")
# TEST_USERNAME = os.getenv("TEST_USERNAME", "admin")
# TEST_PASSWORD = os.getenv("TEST_PASSWORD", "admin")

@allure.feature("Авторизация")
@allure.story("Успешный вход в систему")
def test_simple_login(login_page: Page):  # Измените с page_with_login на login_page
    """Тест: ввести логин/пароль, нажать Войти и проверить результат"""
    print(f"\n[DEBUG] Отправляю: USER='{TEST_USERNAME}', PASS='{TEST_PASSWORD}'")
    with allure.step("Вводим корректные учетные данные"):
        login_page.fill("[data-testid='username-input']", TEST_USERNAME)
        login_page.fill("[data-testid='password-input']", TEST_PASSWORD)
        
    with allure.step("Нажимаем кнопку 'Войти'"):
        login_page.click("[data-testid='submit-btn']")
        
    with allure.step("Проверяем результат входа"):
        login_page.wait_for_timeout(2000)
        current_url = login_page.url
        
        if "login" in current_url:
            error_block = login_page.locator("[data-testid='error-message']")
            if error_block.is_visible():
                error_text = error_block.inner_text().strip()
                raise AssertionError(f"Вход не удался! Сервер вернул ошибку: '{error_text}'")
            else:
                raise AssertionError(f"Вход не удался, но сообщение об ошибке на экране отсутствует. URL: {current_url}")
        
        expect(login_page.locator("#userMenuBtn")).to_be_visible(timeout=10000)