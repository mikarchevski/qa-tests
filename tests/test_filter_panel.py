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

class TestFilterPanel:
    """Тесты отображения файлов с фильтрацией"""

    def test_new_file(self, authenticated_page: Page, temp_file, cleanup_uploaded_files):
              """Тест загрузки файла с проверкой фильтра 'Новые (24ч)'"""
              page = authenticated_page
              
              # 1. Получаем точное имя файла
              file_name = temp_file.name 

              # 2. Загружаем файл
              page.locator("[data-testid='upload-file-btn']").click()
              page.wait_for_timeout(1000)
              page.locator("[data-testid='file-input']").set_input_files(str(temp_file))
              page.locator("[data-testid='file-input']").dispatch_event("change")

              # 3. Ждём завершения загрузки
              upload_item = page.locator(".upload-item").filter(has_text=file_name)
              expect(upload_item).to_be_visible(timeout=10000)
              expect(upload_item).to_contain_text("Готово", timeout=15000)

              # 4. Проверяем, что файл виден в общем списке ("Все файлы")
              file_card = page.locator(".file-card").filter(has_text=file_name)
              expect(file_card).to_be_visible(timeout=5000)

              # 5. Применяем фильтр "Новые (24ч)"
              filter_new = page.locator("[data-testid='filter-btn-new']").click()

              # 6. Проверяем, что файл всё ещё виден
              expect(file_card).to_be_visible(timeout=5000)
              
              # 7. Возвращаемся к "Все файлы" — файл должен остаться
              filter_all = page.locator("[data-testid='filter-btn-all']").click()
              expect(file_card).to_be_visible(timeout=3000)


    def test_new_img(self, authenticated_page: Page, temp_img, cleanup_uploaded_files):
            """Тест загрузки изображения с проверкой фильтрации"""
            page = authenticated_page
    
            # 1. Получаем точное имя файла
            file_name = temp_img.name 

            # 2. Загружаем файл
            page.locator("[data-testid='upload-file-btn']").click()
            page.wait_for_timeout(1000)
            page.locator("[data-testid='file-input']").set_input_files(str(temp_img))
            page.locator("[data-testid='file-input']").dispatch_event("change")

            # 3. Ждём завершения загрузки
            upload_item = page.locator(".upload-item").filter(has_text=file_name)
            expect(upload_item).to_be_visible(timeout=10000)
            expect(upload_item).to_contain_text("Готово", timeout=15000)

            file_card = page.locator(".file-card").filter(has_text=file_name)

            # 4. Теперь применяем фильтр "Фото"
            filter_btn = page.locator("[data-testid='filter-btn-image']").click

            # 5. Проверяем, что файл виден после фильтрации
            file_card = page.locator(".file-card").filter(has_text=file_name)
            expect(file_card).to_be_visible(timeout=5000)
            
    def test_filter_video(self, authenticated_page: Page, temp_video, cleanup_uploaded_files):
            """Тест фильтрации видеофайлов"""
            page = authenticated_page
            file_name = temp_video.name

            # 1. Загружаем видео
            page.locator("[data-testid='upload-file-btn']").click()
            page.wait_for_timeout(1000)
            page.locator("[data-testid='file-input']").set_input_files(str(temp_video))
            page.locator("[data-testid='file-input']").dispatch_event("change")
            
            upload_item = page.locator(".upload-item").filter(has_text=file_name)
            expect(upload_item).to_contain_text("Готово", timeout=15000)

            file_card = page.locator(".file-card").filter(has_text=file_name)

            # 2. Применяем фильтр "Видео"
            filter_video = page.locator("[data-testid='filter-btn-video']").click()

            # 3. Проверяем, что видео видно
            expect(file_card).to_be_visible(timeout=5000)

            # 4. Переключаем на "Фото" — видео должно исчезнуть
            filter_image = page.locator("[data-testid='filter-btn-image']").click()
            expect(file_card).not_to_be_visible(timeout=3000)

            # 5. Возвращаемся к "Все файлы" — видео должно вернуться
            filter_all = page.locator("[data-testid='filter-btn-all']").click()
            expect(file_card).to_be_visible(timeout=3000)
                
