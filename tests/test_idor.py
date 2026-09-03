import pytest
from playwright.sync_api import Page, expect
import os
from dotenv import load_dotenv

load_dotenv()
BASE_URL = os.getenv("APP_URL", "http://localhost:5000")


class TestIDOR:
    """Тесты на межпользовательскую изоляцию (IDOR)"""

    def test_user_b_cannot_delete_user_a_file(self, page: Page, temp_file, test_users):
        """
        Сценарий IDOR:
        1. Пользователь А загружает файл.
        2. Мы извлекаем short_id этого файла из DOM.
        3. Пользователь Б входит в систему.
        4. Пользователь Б пытается удалить файл Пользователя А через прямой API-запрос.
        Ожидаемый результат: 403 Forbidden (или 404 Not Found).
        """
        
        user_a = test_users["user_a"]
        user_b = test_users["user_b"]
        
        # ==========================================
        # ШАГ 1: Пользователь А входит и загружает файл
        # ==========================================
        page.goto(f"{BASE_URL}/login")
        page.locator("[data-testid='username-input']").fill(user_a["username"])
        page.locator("[data-testid='password-input']").fill(user_a["password"])
        page.locator("[data-testid='submit-btn']").click()
        
        # Ждем загрузки главной страницы
        expect(page.locator("[data-testid='files-list-container']")).to_be_visible(timeout=10000)

        file_name = temp_file.name
        page.locator("[data-testid='upload-file-btn']").click()
        page.wait_for_timeout(500)
        page.locator("[data-testid='file-input']").set_input_files(str(temp_file))
        
        # Ждем завершения загрузки
        upload_item = page.locator(".upload-item").filter(has_text=file_name)
        expect(upload_item).to_contain_text("Готово", timeout=15000)

                # ==========================================
        # ШАГ 2: Получаем short_id через API
        # ==========================================
        # Делаем GET-запрос к /api/files, используя куки текущей сессии (Пользователь А)
        # page.request автоматически передает все куки и заголовки
        files_response = page.request.get(f"{BASE_URL}/api/files")
        assert files_response.status == 200, f"Не удалось получить список файлов: {files_response.status}"
        
        files_data = files_response.json()
        files_list = files_data.get("files", [])
        
        # Ищем наш файл по имени
        target_file = None
        for file_info in files_list:
            if file_info.get("filename") == file_name:
                target_file = file_info
                break
        
        assert target_file is not None, f"Файл '{file_name}' не найден в списке /api/files"
        
        short_id = target_file.get("url")
        assert short_id and len(short_id) > 0, f"short_id пуст или некорректен: {short_id}"
        
        print(f"✅ Извлечен short_id для файла '{file_name}': {short_id}")

        # ==========================================
        # ШАГ 3: Пользователь Б входит в систему
        # ==========================================
        page.goto(f"{BASE_URL}/logout")
        page.goto(f"{BASE_URL}/login")
        
        page.locator("[data-testid='username-input']").fill(user_b["username"])
        page.locator("[data-testid='password-input']").fill(user_b["password"])
        page.locator("[data-testid='submit-btn']").click()
        
        expect(page.locator("[data-testid='files-list-container']")).to_be_visible(timeout=10000)

        # ==========================================
        # ШАГ 4: Пользователь Б пытается удалить файл через API
        # ==========================================
        delete_url = f"{BASE_URL}/api/delete/{short_id}"
        response = page.request.delete(delete_url)
        
        # ==========================================
        # ШАГ 5: Проверка результата
        # ==========================================
        assert response.status in [403, 404], \
            f"🚨 IDOR УЯЗВИМОСТЬ! Пользователь Б смог удалить файл Пользователя А. Статус: {response.status}, Ответ: {response.text()}"