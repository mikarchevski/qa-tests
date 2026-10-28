import os
import pytest
from playwright.sync_api import expect
from Pages.upload_page import UploadPage
from config import Config
from pathlib import Path

from conftest import upload_page

def test_manager_panel_isavailable(upload_page: UploadPage, temp_file: Path, cleanup_uploaded_files):
    upload_page.page.wait_for_load_state("networkidle")
    upload_page.upload_single_file(str(temp_file))
    expect(upload_page.get_file_in_list(str(temp_file.name))).to_be_visible()
    upload_page.click_file(str(temp_file.name))
    expect(upload_page.manage_panel).to_be_visible()

def test_manager_panel_iscontain_filename(upload_page: UploadPage,temp_file: Path, cleanup_uploaded_files):
    upload_page.page.wait_for_load_state("networkidle")
    upload_page.upload_single_file(str(temp_file))
    upload_page.click_file(str(temp_file.name))
    expect(upload_page.manage_panel_filename).to_be_visible()

def test_manager_panel_iscontain_download_button(upload_page: UploadPage, temp_file: Path, cleanup_uploaded_files):
    upload_page.page.wait_for_load_state("networkidle")
    upload_page.upload_single_file(str(temp_file))
    upload_page.click_file(str(temp_file.name))
    expect(upload_page.download_button).to_be_visible()

def test_manage_panel_iscontain_copy_button(upload_page: UploadPage, temp_file: Path, cleanup_uploaded_files):
    upload_page.page.wait_for_load_state("networkidle")
    upload_page.upload_single_file(str(temp_file))
    upload_page.click_file(str(temp_file.name))
    expect(upload_page.copy_button).to_be_visible()

def test_manage_panel_iscontain_delete_button(upload_page: UploadPage, temp_file: Path, cleanup_uploaded_files):
    upload_page.page.wait_for_load_state("networkidle")
    upload_page.upload_single_file(str(temp_file))
    upload_page.click_file(str(temp_file.name))
    expect(upload_page.delete_button).to_be_visible()

def test_manage_panel_iscontain_close_button(upload_page: UploadPage, temp_file: Path, cleanup_uploaded_files):
    upload_page.page.wait_for_load_state("networkidle")
    upload_page.upload_single_file(str(temp_file))
    upload_page.click_file(str(temp_file.name))
    expect(upload_page.manage_panel_close_button).to_be_visible()

def test_close_manage_panel(upload_page: UploadPage, temp_file: Path, cleanup_uploaded_files):
    upload_page.page.wait_for_load_state("networkidle")
    upload_page.upload_single_file(str(temp_file))
    upload_page.click_file(str(temp_file.name))
    upload_page.manage_panel_close_button.click()
    expect(upload_page.manage_panel).not_to_be_visible()

def test_file_name_changed_in_manage_panel(upload_page: UploadPage, temp_files: list[Path], cleanup_uploaded_files):
    upload_page.page.wait_for_load_state("networkidle")
    upload_page.upload_multiple_files([str(p) for p in temp_files])
    upload_page.click_file(temp_files[0].name)
    expect(upload_page.manage_panel).to_be_visible()
    expect(upload_page.manage_panel_filename).to_contain_text(temp_files[0].name)
    upload_page.click_file(temp_files[1].name)
    expect(upload_page.manage_panel_filename).to_contain_text(temp_files[1].name)
