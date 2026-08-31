import pytest
from pathlib import Path
import tempfile

@pytest.fixture
def temp_file(tmp_path):
    """Создаёт временный файл для загрузки"""
    file = tmp_path / "test_upload.txt"
    file.write_text("Hello from Playwright test!")
    return file

@pytest.fixture
def multiple_files(tmp_path):
    """Создаёт несколько временных файлов"""
    files = []
    for i in range(3):
        file = tmp_path / f"test_file_{i}.txt"
        file.write_text(f"Content of file {i}")
        files.append(file)
    return files

@pytest.fixture
def large_file(tmp_path):
    """Создаёт большой файл для теста отмены загрузки"""
    file = tmp_path / "large_file.bin"
    # 50 МБ — достаточно большой, чтобы успеть нажать отмену
    file.write_bytes(b"0" * (50 * 1024 * 1024))
    return file