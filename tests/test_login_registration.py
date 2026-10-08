from playwright.sync_api import expect
from Pages.login_page import LoginPage
from config import Config
import pytest


# Простой вход на сайт с валидными данными
def test_success_login(login_page: LoginPage):
    login_page.fill_login(Config.TEST_USERNAME, Config.TEST_PASSWORD)
    login_page.send_login_form()
    expect(login_page.page).to_have_url(Config.BASE_URL + "/")


# Вход с невалидным паролем
def test_error_login(login_page: LoginPage):
    login_page.fill_login(Config.TEST_USERNAME, Config.INVALID_PASSWORD)
    login_page.send_login_form()
    expect(login_page.page).to_have_url(Config.BASE_URL + "/login")


# Отправка пустой формы входа
def test_empty_form(login_page: LoginPage):
    login_page.fill_login("", "")
    login_page.send_login_form()
    expect(login_page.page.locator("#usernameError")).to_be_visible()
    expect(login_page.page.locator("#passwordError")).to_be_visible()


# Скрытие ошибок под полями после изменения значения полей
def test_refill_form(login_page: LoginPage):
    login_page.fill_login("", "")
    login_page.send_login_form()
    expect(login_page.page.locator("#usernameError")).to_be_visible()
    login_page.fill_login(Config.TEST_USERNAME, Config.TEST_PASSWORD)
    login_page.send_login_form()
    expect(login_page.page.locator("#usernameError")).not_to_be_visible()
    expect(login_page.page).to_have_url(Config.BASE_URL + "/")


# Переключение на регистрацию и обратно
def test_open_reg_and_login(login_page: LoginPage):
    login_page.login_reg_link.click()
    expect(login_page.page.get_by_test_id("password-confirm-input")).to_be_visible()
    login_page.login_reg_link.click()
    expect(login_page.page.get_by_test_id("password-confirm-input")).not_to_be_visible()


# Отображение формы регистрации
def test_open_reg_form(login_page: LoginPage):
    login_page.login_reg_link.click()
    expect(login_page.page.get_by_test_id("password-confirm-input")).to_be_visible()
    expect(login_page.page.get_by_test_id("invite-code-input")).to_be_visible()


# Отправка пустой формы регистрации
def test_empty_reg_form(login_page: LoginPage):
    login_page.login_reg_link.click()
    login_page.fill_registration("", "", "", "")
    login_page.send_reg_form()
    expect(login_page.page.locator("#inviteCodeError")).to_be_visible()
    expect(login_page.page).to_have_url(Config.BASE_URL + "/login")


# Скрытие ошибок валидации после ввода данных


# Регистрация нового пользователя
def test_new_user_register(login_page: LoginPage, valid_invite_code: str):
    login_page.login_reg_link.click()
    unique_user = Config.unique_username()
    login_page.fill_registration(unique_user, Config.REG_PASSWORD, Config.REG_PASSWORD, valid_invite_code)
    login_page.send_reg_form()
    expect(login_page.page).to_have_url(Config.BASE_URL + "/")


# Скрытие ошибок под полями при переключении между входом и регистрацией
@pytest.mark.skip(reason="BUG: Ошибки валидации не исчезают после повторного ввода данных ")
def test_hide_validation_errors(login_page: LoginPage):
    login_page.login_reg_link.click()
    login_page.fill_registration("", "", "", "")
    login_page.send_reg_form()
    expect(login_page.page.locator("#inviteCodeError")).to_be_visible()
    login_page.fill_registration(Config.REG_USERNAME, Config.REG_PASSWORD, Config.REG_PASSWORD, "test11")
    expect(login_page.page.locator("#inviteCodeError")).not_to_be_visible()


# Показ сообщение об ошибках над формой регистрации
@pytest.mark.skip(reason="BUG: Сообщение не пропадает при переключении")
def test_show_error_message(login_page: LoginPage):
    login_page.login_reg_link.click()
    login_page.fill_registration(Config.REG_USERNAME, Config.REG_PASSWORD, Config.REG_PASSWORD, "test12")
    login_page.send_reg_form()
    expect(login_page.error_message).to_be_visible()
    login_page.login_reg_link.click()
    expect(login_page.error_message).not_to_be_visible()
