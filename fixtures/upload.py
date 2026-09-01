import pytest
import subprocess
from pathlib import Path
from PIL import Image
import tempfile


@pytest.fixture
def temp_file(tmp_path):
    """Создаёт временный файл для загрузки"""
    file = tmp_path / "test_upload.txt"
    file.write_text("Hello from Playwright test!")
    return file

@pytest.fixture
def temp_img(tmp_path):
    """Создаёт временную картинку для загрузки"""
    file = tmp_path / "test_upload.png"
    img = Image.new('RGB', (100, 100), color='red')
    img.save(str(file), 'PNG')
    return file

@pytest.fixture
def temp_video(tmp_path):
    """Использует готовое видео из test_data/"""
    test_data_dir = Path(__file__).parent / "test_data"
    video_file = test_data_dir / "sample_video.mp4"    
    return video_file

@pytest.fixture
def temp_img(tmp_path):
    """Создаёт временный файл для загрузки"""
    file = tmp_path / "test_upload.png"
    img = Image.new('RGB', (100, 100), color='red')
    img.save(str(file), 'PNG')
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