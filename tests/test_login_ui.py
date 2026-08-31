# -*- coding: utf-8 -*-
import pytest
import allure
from playwright.sync_api import Page, expect
from conftest import BASE_URL, TEST_USERNAME, TEST_PASSWORD

@allure.feature("Авторизация")
@allure.story("Успешный вход в систему")
def test_simple_login(page_with_login: Page):
    """Тест: ввести логин/пароль, нажать Войти и проверить результат"""
    print(f"\n[DEBUG] Отправляю: USER='{TEST_USERNAME}', PASS='{TEST_PASSWORD}'")
    with allure.step("Вводим корректные учетные данные"):
        page_with_login.fill("[data-testid='username-input']", TEST_USERNAME)
        page_with_login.fill("[data-testid='password-input']", TEST_PASSWORD)
        
    with allure.step("Нажимаем кнопку 'Войти'"):
        page_with_login.click("[data-testid='submit-btn']")
        
    with allure.step("Проверяем результат входа"):
        # Даем странице 2 секунды на ответ сервера и редирект
        page_with_login.wait_for_timeout(2000)
        current_url = page_with_login.url
        
        # Если мы всё ещё на странице логина, значит вход не удался
        if "login" in current_url:
            # Проверяем, есть ли на экране сообщение об ошибке от сервера
            error_block = page_with_login.locator("[data-testid='error-message']")
            if error_block.is_visible():
                error_text = error_block.inner_text().strip()
                raise AssertionError(f"Вход не удался! Сервер вернул ошибку: '{error_text}'")
            else:
                raise AssertionError(f"Вход не удался, но сообщение об ошибке на экране отсутствует. URL: {current_url}")
        
        # Если мы дошли до сюда, значит "login" нет в URL. Проверяем элемент успеха.
        expect(page_with_login.locator("#userMenuBtn")).to_be_visible(timeout=10000)