import os
import pytest
from playwright.sync_api import expect
from Pages.upload_page import UploadPage
from config import Config
from pathlib import Path

from conftest import upload_page


# загрузка файла
def test_successful_file_upload(upload_page: UploadPage, temp_file: Path, cleanup_uploaded_files):
    upload_page.page.wait_for_load_state("networkidle")
    upload_page.upload_single_file(str(temp_file))
    # Проверяем статус в виджете загрузки
    status = upload_page.get_upload_status("test_automation_file.txt")
    expect(status).to_contain_text("Готово")
    # Проверяем, что файл появился в общем списке
    file_card = upload_page.get_file_in_list("test_automation_file.txt")
    expect(file_card).to_be_visible()


# повторная загрузка уже загруженного файла
def test_re_upload_file(upload_page: UploadPage, temp_file: Path, cleanup_uploaded_files):
    upload_page.page.wait_for_load_state("networkidle")
    file_name = "test_automation_file.txt"

    # 1. ПЕРВАЯ ЗАГРУЗКА
    upload_page.upload_single_file(str(temp_file))

    # Ждем, пока первая загрузка точно завершится
    status_first = upload_page.get_upload_status(file_name)
    expect(status_first).to_contain_text("Готово")
    #
    # # 2. ВТОРАЯ ЗАГРУЗКА (того же самого файла)
    upload_page.upload_single_file(str(temp_file))
    status_second = upload_page.get_upload_status(file_name).first
    expect(status_second).to_contain_text("уже загружен")


# Загрузка нескольких файлов
def test_upload_multiple_files(
        upload_page: UploadPage,
        temp_files: list[Path],
        cleanup_uploaded_files
):
    """Сценарий: загрузка нескольких файлов одновременно"""
    upload_page.page.wait_for_load_state("networkidle")

    # 1. Загружаем все 3 файла за один раз
    upload_page.upload_multiple_files([str(p) for p in temp_files])

    # 2. Проверяем, что каждый файл появился в виджете загрузки
    for file_path in temp_files:
        file_name = file_path.name
        status = upload_page.get_upload_status(file_name)
        expect(status).to_contain_text("Готово")


# Загрузка каталога
def test_upload_folder(upload_page: UploadPage, temp_folder: Path, cleanup_uploaded_files):
    upload_page.page.wait_for_load_state("networkidle")
    upload_page.upload_folder(str(temp_folder))
    status = upload_page.get_upload_status(temp_folder.name)
    expect(status).to_contain_text("Готово")
    folder_exist = upload_page.get_file_in_list(str(temp_folder.name))
    expect(folder_exist).to_be_visible()


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


# Сценарий: проверка факта скачивания файла
def test_download_file(upload_page: UploadPage, temp_file: Path, cleanup_uploaded_files):
    upload_page.page.wait_for_load_state("networkidle")

    file_name = temp_file.name

    # 1. Загружаем файл
    upload_page.upload_single_file(str(temp_file))
    expect(upload_page.get_file_in_list(file_name)).to_be_visible()

    # 2. Кликаем по файлу (выделяем его, чтобы появилась кнопка скачивания)
    upload_page.get_file_in_list(file_name).click()

    # 3. Перехватываем событие скачивания
    with upload_page.page.expect_download() as download_info:
        upload_page.download_button.click()

    # 4. Проверяем факт скачивания
    download = download_info.value
    assert download.suggested_filename == file_name
    assert download.failure() is None
