# -*- coding: utf-8 -*-
import pytest
import allure
from playwright.sync_api import Page, expect

@allure.feature("Авторизация")
@allure.story("Ошибка входа в систему")
def test_login_with_invalid_credentials(login_page: Page):  # Измените с page_with_login на login_page
    """Тест: проверка отображения ошибки при неверном логине/пароле"""

    with allure.step("Вводим заведомо неверные учетные данные"):
        login_page.fill("[data-testid='username-input']", "wrong_user_xyz")
        login_page.fill("[data-testid='password-input']", "wrong_password_123")

    with allure.step("Нажимаем кнопку 'Войти'"):
        login_page.click("[data-testid='submit-btn']")

    with allure.step("Проверяем появление сообщения об ошибке"):
        error_block = login_page.locator("[data-testid='error-message']")
        expect(error_block).to_be_visible(timeout=5000)

    with allure.step("Проверяем, что текст ошибки не пустой"):
        error_text = error_block.inner_text().strip()
        assert error_text != "", "Сообщение об ошибке есть, но текст внутри пустой!"
        allure.attach(error_text, name="Текст ошибки от сервера", attachment_type=allure.attachment_type.TEXT)

    with allure.step("Проверяем, что мы остались на странице логина"):
        assert "login" in login_page.url, f"При ошибке входа URL изменился на: {login_page.url}"