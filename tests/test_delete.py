import os
import pytest
from playwright.sync_api import expect
from Pages.upload_page import UploadPage
from config import Config
from pathlib import Path

from conftest import upload_page

# Удаление файла через UI
def test_ui_delete(upload_page: UploadPage, temp_file: Path, cleanup_uploaded_files):
    upload_page.page.wait_for_load_state("networkidle")
    # 1. Загружаем файл
    upload_page.upload_single_file(str(temp_file))
    # 2. Ждем, пока файл появится в списке
    file_card = upload_page.get_file_in_list(temp_file.name)
    expect(file_card).to_be_visible()
    # 3. Удаляем через UI
    upload_page.delete_file_via_ui(temp_file.name)

def test_ui_delete_several_files(upload_page: UploadPage, temp_files: list[Path], cleanup_uploaded_files):
    upload_page.page.wait_for_load_state("networkidle")
    upload_page.upload_multiple_files([str(p) for p in temp_files])
    file_names = [p.name for p in temp_files]
    for name in file_names:
        expect(upload_page.get_file_in_list(name)).to_be_visible()
    files_to_delete = file_names[:2]
    file_to_keep = file_names[2]

    for file_name in files_to_delete:
        upload_page.delete_file_via_ui(file_name)

    # 4. Проверяем, что удаленные файлы исчезли
    for file_name in files_to_delete:
        expect(upload_page.get_file_in_list(file_name)).not_to_be_visible()

    # 5. Проверяем, что третий файл остался
    expect(upload_page.get_file_in_list(file_to_keep)).to_be_visible()

@pytest.mark.skip(reason="BUG: каталог криво загружается и соотвественно не удаляется ")
def test_ui_delete_folder(upload_page: UploadPage,temp_folder: Path, cleanup_uploaded_files):
    upload_page.page.wait_for_load_state("networkidle")
    upload_page.upload_folder(str(temp_folder))
    folder_exist = upload_page.get_file_in_list(str(temp_folder.name))
    expect(folder_exist).to_be_visible()
    upload_page.delete_file_via_ui(str(temp_folder.name))

def test_ui_delete_photo_with_filter(upload_page: UploadPage, test_image: Path, temp_file: Path, cleanup_uploaded_files):
    upload_page.page.wait_for_load_state("networkidle")
    upload_page.upload_multiple_files([str(test_image), str(temp_file)])
    upload_page.img_files_filter.click()
    upload_page.delete_file_via_ui(str(test_image.name))
    upload_page.all_files_filter.click()
    expect(upload_page.get_file_in_list(test_image.name)).not_to_be_visible()
    expect(upload_page.get_file_in_list(temp_file.name)).to_be_visible()
