import os
from typing import cast

import pytest
from playwright.sync_api import expect
from Pages.upload_page import UploadPage
from Pages.login_page import LoginPage
from config import Config
from pathlib import Path

from conftest import upload_page

# Базовый тест наличия пользовательского меню
def test_user_menu_uname(upload_page: UploadPage):
    upload_page.open()
    upload_page.open_user_menu()

# Проверка корректности отображения имени пользователя в меню
def test_user_name_isavailable(upload_page: UploadPage):
    upload_page.open()
    upload_page.open_user_menu()
    expect(upload_page.user_menu_uname).to_be_visible()
    expect(upload_page.user_menu_uname).to_contain_text(Config.TEST_USERNAME)


def test_theme_toggle(upload_page: UploadPage):
    """Сценарий: переключение темы меняет атрибут data-theme на <html>"""
    upload_page.open()
    upload_page.open_user_menu()
    button_text = upload_page.user_menu_theme_toggle.inner_text().strip()
    expected_theme = "dark" if "Тёмная" in button_text else "light"
    upload_page.user_menu_theme_toggle.click()
    expect(upload_page.page.locator("html")).to_have_attribute("data-theme", expected_theme)

def test_logout(upload_page: UploadPage, login_page: LoginPage):
    upload_page.open()
    upload_page.open_user_menu()
    upload_page.user_menu_logout_btn.click()
    expect(login_page.page).to_have_url(Config.BASE_URL + "/login")