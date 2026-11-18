# API Документация Uploader

Базовый URL: `http://127.0.0.1:5000` (или `Config.BASE_URL`)
Все запросы, кроме `/login`, требуют авторизации (активная сессия Flask или cookie).

## 1. Получение списка файлов

- **Метод:** `GET /api/files`
- **Параметры (query):**
  - `page` (int, default: 1)
  - `per_page` (int, default: 20, max: 100)
  - `sort` (str, default: 'upload_date')
  - `order` (str, default: 'DESC' или 'ASC')
  - `folder` (str, optional)
- **Ответ (200 OK):**
  ```json
  {
    "files": [
      {
        "short_id": "abc123",
        "filename": "test.txt",
        "size": "1.2 KB",
        "date": "2023-10-25",
        "downloads": 0,
        "url": "/d/abc123",
        "folder_path": ""
      }
    ],
    "total": 1,
    "page": 1,
    "per_page": 20,
    "pages": 1
  }
  ```

## 2. Удаление файла

Метод: DELETE /api/delete/<short_id>
Заголовки: Требуется X-CSRFToken (если включен CSRF) или активная сессия.
Ответ (200 OK): {"success": true, "message": "File deleted"}

## 3. Массовое удаление файлов

Метод: POST /api/delete/bulk
Тело запроса (JSON):
{ "short_ids": ["abc123", "def456"] }
// ИЛИ
{ "folder_path": "/my_folder" }

Ответ (200 OK):

{
"success": true,
"deleted_count": 2,
"errors": []
}

## 4. Загрузка файла

Метод: POST /upload
Content-Type: multipart/form-data
Поля:
file: (binary) сам файл
hash: (str) SHA-256 хэш файла (для проверки дубликатов)
folder_path: (str, optional)
Ответ (200 OK):

{
"success": true,
"message": "File uploaded successfully",
"file_data": {
"short_id": "xyz789",
"filename": "test.txt",
"size": "1.2 KB",
"date": "2023-10-25",
"downloads": 0,
"url": "/d/xyz789",
"folder_path": ""
}
}
