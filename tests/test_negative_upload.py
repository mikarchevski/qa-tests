import pytest
from playwright.sync_api import Page, expect
import os
from dotenv import load_dotenv

load_dotenv()
BASE_URL = os.getenv("APP_URL", "http://localhost:5000")


class TestNegativeUpload:
    """Негативные сценарии загрузки файлов"""

    def test_upload_empty_file(self, authenticated_page, tmp_path, cleanup_uploaded_files):
        """Проверка реакции системы на загрузку пустого файла"""
        page = authenticated_page
        empty_file = tmp_path / "empty_file.txt"
        empty_file.write_text("") # Создаем файл 0 байт
        
        page.locator("[data-testid='upload-file-btn']").click()
        page.wait_for_timeout(500)
        page.locator("[data-testid='file-input']").set_input_files(str(empty_file))
        
        # Ожидаем, что система либо покажет понятную ошибку, либо корректно обработает (зависит от ТЗ)
        # Например, проверка, что не появилось зависшее состояние "Загрузка..."
        error_msg = page.locator("[data-testid='error-message']")
        if error_msg.is_visible():
            expect(error_msg).to_contain_text("пуст") # или другой ожидаемый текст ошибки
        else:
            # Если пустые файлы разрешены, проверяем, что загрузка завершилась
            upload_item = page.locator(".upload-item").filter(has_text="empty_file.txt")
            expect(upload_item).to_contain_text("Готово", timeout=10000)

    def test_upload_file_with_special_chars(self, authenticated_page, tmp_path, cleanup_uploaded_files):
        """Загрузка файла с кириллицей, пробелами и спецсимволами"""
        page = authenticated_page
        weird_file = tmp_path / "файл с пробелами и #_@.txt"
        weird_file.write_text("test content")
        
        page.locator("[data-testid='upload-file-btn']").click()
        page.wait_for_timeout(500)
        page.locator("[data-testid='file-input']").set_input_files(str(weird_file))
        
        upload_item = page.locator(".upload-item").filter(has_text="файл с пробелами")
        expect(upload_item).to_contain_text("Готово", timeout=15000)