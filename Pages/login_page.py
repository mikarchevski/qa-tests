from playwright.sync_api import Page


class LoginPage:
    def __init__(self, page: Page):
        self.page = page
        self.username_input = page.get_by_test_id("username-input")
        self.password_input = page.get_by_test_id("password-input")
        self.login_btn = page.get_by_test_id("submit-btn")
        self.login_reg_link = page.get_by_test_id("toggle-link")
        self.confirm_password_input = page.get_by_test_id("password-confirm-input")
        self.invite_token = page.get_by_test_id("invite-code-input")
        self.error_message = page.get_by_test_id("error-message")

    def fill_login(self, username: str, password: str):
        self.username_input.fill(username)
        self.password_input.fill(password)

    def send_login_form(self):
        self.login_btn.click()

    def fill_registration(self, username: str, password: str, confirm_password: str, invite_token: str):
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.confirm_password_input.fill(confirm_password)
        self.invite_token.fill(invite_token)

    def send_reg_form(self):
        self.login_btn.click()

    def goto(self):
        self.page.goto("http://127.0.0.1:5000/login")
