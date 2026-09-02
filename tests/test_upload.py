import pytest
from playwright.sync_api import Page, expect
import os
from dotenv import load_dotenv

load_dotenv()
BASE_URL = os.getenv("APP_URL", "http://localhost:5000")


@pytest.fixture(scope="function")
def authenticated_page(page: Page):
    """Авторизация перед тестом"""
    page.goto(f"{BASE_URL}/login")
    # ПРАВИЛЬНЫЕ селекторы (как в test_login_ui.py)
    page.locator("[data-testid='username-input']").fill(os.getenv("TEST_USERNAME", "admin"))
    page.locator("[data-testid='password-input']").fill(os.getenv("TEST_PASSWORD", "admin"))
    page.locator("[data-testid='submit-btn']").click()
    # Ждём, пока загрузится главная страница
    expect(page.locator("[data-testid='files-list-container']")).to_be_visible(timeout=10000)
    yield page


class TestFileUpload:
    """Тесты загрузки файлов"""
    def test_upload_single_file(self, authenticated_page: Page, temp_file, cleanup_uploaded_files):
        """
        Базовый тест: загрузка одного файла.
        Работает напрямую с нативным <input type="file">, без клика по кастомной кнопке.
        """
        page = authenticated_page
        
        # 1. Получаем точное имя файла (например, "test_upload_1a2b3c4d.txt")
        file_name = temp_file.name 

        # 2. Инициируем действие выбора файла (клик по кнопке)
        page.locator("[data-testid='upload-file-btn']").click()
        
        # 3. Микро-задержка: даем JS 300мс обработать клик и подготовить инпут
        page.wait_for_timeout(1000)

        # 4. Устанавливаем файл напрямую в скрытый инпут
        file_input = page.locator("[data-testid='file-input']")
        file_input.set_input_files(str(temp_file))

        # 5. Ожидаем появления элемента в панели загрузок
        upload_item = page.locator(".upload-item").filter(has_text=file_name)
        expect(upload_item).to_be_visible(timeout=10000)

        # 6. Ожидаем завершения загрузки 
        # (Если у вас в UI написано "Загружено" или "✅", замените "Готово" на этот текст)
        expect(upload_item).to_contain_text("Готово", timeout=15000)

        # 7. Проверяем, что файл появился в основной сетке файлов
        file_card = page.locator(".file-card").filter(has_text=file_name)
        expect(file_card).to_be_visible(timeout=10000)

    def test_upload_multiple_files(self, authenticated_page: Page, multiple_files, cleanup_uploaded_files):
        """Загрузка нескольких файлов одновременно"""
        page = authenticated_page

        page.locator("[data-testid='upload-file-btn']").click()

        page.wait_for_timeout(1000)

        file_input = page.locator("[data-testid='file-input']")
        file_input.set_input_files([str(f) for f in multiple_files])

        # Проверяем, что все 3 файла появились в панели загрузок
        upload_items = page.locator(".upload-item")
        expect(upload_items).to_have_count(3, timeout=10000)

        # Ждём, пока все загрузятся
        for file in multiple_files:
            item = page.locator(".upload-item").filter(has_text=file.stem)
            expect(item).to_contain_text("Готово", timeout=30000)

    def test_upload_folder(self, authenticated_page: Page, tmp_path, cleanup_uploaded_files):
        """Загрузка папки через folderInput"""
        page = authenticated_page

        # Создаём структуру папки
        test_folder = tmp_path / "test_folder"
        test_folder.mkdir()
        (test_folder / "file1.txt").write_text("content 1")
        (test_folder / "file2.txt").write_text("content 2")

        page.locator("[data-testid='upload-folder-btn']").click()
        page.wait_for_timeout(1000)

        folder_input = page.locator("[data-testid='folder-input']")
        folder_input.set_input_files(str(test_folder))

        # Проверяем, что папка появилась в панели загрузок
        folder_item = page.locator(".upload-item").filter(has_text="test_folder")
        expect(folder_item).to_be_visible(timeout=10000)

        # Ждём завершения загрузки папки
        expect(folder_item).to_contain_text("Готово", timeout=15000)

        file_card = page.locator(".file-card").filter(has_text="test_folder")
        expect(file_card).to_be_visible(timeout=10000)

    def test_upload_duplicate_file(self, authenticated_page: Page, temp_file, cleanup_uploaded_files):
        """Повторная загрузка того же файла"""
        page = authenticated_page

        # Первая загрузка
        page.locator("[data-testid='upload-file-btn']").click()
        page.wait_for_timeout(1000)
        page.locator("[data-testid='file-input']").set_input_files(str(temp_file))

        first_item = page.locator(".upload-item").filter(has_text="test_upload").first
        expect(first_item).to_contain_text("Готово", timeout=1000)

        page.wait_for_timeout(1000)

        # Вторая загрузка того же файла
        page.locator("[data-testid='upload-file-btn']").click()
        page.locator("[data-testid='file-input']").set_input_files(str(temp_file))

        # Проверяем реакцию на дубликат (текст зависит от вашего UI)
        second_item = page.locator(".upload-item").filter(has_text="test_upload").first
        expect(second_item).to_contain_text("Пропуск", timeout=1000)