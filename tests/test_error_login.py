# -*- coding: utf-8 -*-
import pytest
import allure
from playwright.sync_api import Page, expect

@allure.feature("Авторизация")
@allure.story("Ошибка входа в систему")
def test_login_with_invalid_credentials(page_with_login: Page):
    """Тест: проверка отображения ошибки при неверном логине/пароле"""

    with allure.step("Вводим заведомо неверные учетные данные"):
        page_with_login.fill("[data-testid='username-input']", "wrong_user_xyz")
        page_with_login.fill("[data-testid='password-input']", "wrong_password_123")

    with allure.step("Нажимаем кнопку 'Войти'"):
        page_with_login.click("[data-testid='submit-btn']")

    with allure.step("Проверяем появление сообщения об ошибке"):
        # Находим блок ошибки
        error_block = page_with_login.locator("[data-testid='error-message']")
        
        # expect автоматически ждет до 5 секунд, пока элемент не станет видимым.
        # Если он не появится - тест УПАДЕТ, и наш хук из conftest.py автоматически сделает скриншот!
        expect(error_block).to_be_visible(timeout=5000)

    with allure.step("Проверяем, что текст ошибки не пустой"):
        error_text = error_block.inner_text().strip()
        assert error_text != "", "Сообщение об ошибке есть, но текст внутри пустой!"
        
        # Логируем текст ошибки в отчет Allure для наглядности
        allure.attach(error_text, name="Текст ошибки от сервера", attachment_type=allure.attachment_type.TEXT)

    with allure.step("Проверяем, что мы остались на странице логина"):
        # При ошибке входа редиректа быть не должно
        assert "login" in page_with_login.url, f"При ошибке входа URL изменился на: {page_with_login.url}"