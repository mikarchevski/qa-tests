from playwright.sync_api import Page, expect


class UploadPage:
    def __init__(self, page: Page):
        self.page = page
        self.upload_input = page.get_by_test_id("file-input")
        self.upload_folder_input = page.get_by_test_id("folder-input")
        self.upload_file_button = page.get_by_test_id("upload-file-btn")
        self.upload_folder_button = page.get_by_test_id("upload-folder-btn")
        self.file_container = page.get_by_test_id("files-list-container")
        self.upload_manager = page.get_by_test_id("upload-manager")
        self.delete_button = page.get_by_test_id("btn-delete")
        self.download_button = page.get_by_test_id("btn-download")
        self.copy_button = page.get_by_test_id("btn-copy-link")
        self.modal_window = page.get_by_test_id("modal-content")
        self.modal_window_confirm = page.get_by_test_id("confirm-delete-btn")
        self.modal_window_close = page.get_by_test_id("cancel-delete-btn")

    def upload_single_file(self, file_path: str):
        """
        Принудительная загрузка файла, обходящая ограничения кастомных UI-компонентов.
        """
        input_el = self.upload_input

        # 1. Делаем скрытый инпут видимым для браузера (снимаем hidden и display: none)
        input_el.evaluate("el => { el.style.display = 'block'; el.hidden = false; }")

        # 2. Вставляем файл
        input_el.set_input_files(file_path)

    def upload_multiple_files(self, file_paths: list[str]):
        """
        Загружает несколько файлов за один раз.
        Playwright принимает список путей, если инпут имеет атрибут 'multiple'.
        """
        # Передаем ВСЕ пути одним списком!
        self.upload_input.set_input_files(file_paths)

    def upload_folder(self, folder_path: str):
        self.upload_folder_input.set_input_files(folder_path)

    def delete_file_via_ui(self, file_name: str):
        # 1. Находим и кликаем по файлу (выделяем его)
        file_card = self.get_file_in_list(file_name)
        file_card.click()

        # 2. Нажимаем кнопку удаления
        self.delete_button.click()

        # 3. Ждем появления модального окна подтверждения
        expect(self.modal_window).to_be_visible()

        # 4. Подтверждаем удаление
        self.modal_window_confirm.click()

        # 5. Ждем, пока файл исчезнет из списка
        expect(file_card).not_to_be_visible()

    # === ЛОКАТОРЫ (тест сам решает, что проверять) ===

    def get_upload_widget(self, file_name: str):
        """Возвращает виджет загрузки для конкретного файла"""
        return self.page.locator(".upload-item").filter(has_text=file_name)

    def get_upload_status(self, file_name: str):
        """Возвращает статус внутри виджета конкретного файла"""
        return self.get_upload_widget(file_name).locator(".item-status")

    def get_file_in_list(self, file_name: str):
        """Возвращает карточку файла в общем списке"""
        return self.file_container.locator(f'[title="{file_name}"]')
