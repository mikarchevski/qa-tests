# Быстрый старт
### Склонировать репозиторий
### Активировать виртуальное окружение
```python3 -m venv venv```
### Поставить зависимости 
```pip install -r requirements.txt```
### Ставим playwright 
```playwright install```
### Настройка окружения
```cp .env.example .env```

```
# Для тестирования локально запущенного uploader:
APP_URL=http://127.0.0.1:5000

# Для тестирования продакшена (как в примере):
# APP_URL=https://benx-share.duckdns.org

TEST_USERNAME=test_user_qa
TEST_PASSWORD=TestPassword123!
```
