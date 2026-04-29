# API для сервиса сокращения ссылок – shortist

Домашнее задание по FastAPI в рамках курса "Прикладной Python".

> **ИПР ДЗ2:** Этот форк содержит тестовое покрытие сервиса shortist — юнит- и функциональные тесты (`tests/`), отчёт покрытия (`htmlcov/`), нагрузочный тест Locust (`locustfile.py`) и сохранённый HTML-отчёт прогона (`locust_report.html`). Все инструкции по воспроизведению — в этом README ниже.

## Описание API

Этот сервис предоставляет REST API для:
- Аутентификации пользователей (регистрация, вход, выход)
- Создания, управления и отслеживания сокращенных ссылок
- Получения статистики по ссылкам

API разделен на две основные группы эндпоинтов:
- `/auth` - для работы с пользователями
- `/links` - для работы со ссылками

## Примеры запросов

### Аутентификация

#### Регистрация нового пользователя
```http
POST /auth/register

{
  "email": "user@example.com",
  "password": "string",
  "is_active": true,
  "is_superuser": false,
  "is_verified": false
}
```

#### Вход пользователя
```http
POST /auth/jwt/login
grant_type=password&username=username@example.com&password=password
```

#### Выход пользователя
```http
POST /auth/jwt/logout
```

### Работа со ссылками
#### Создание сокращенной ссылки
```http
POST /links/shorten

{
"original_url": "https://example.com",
"custom_alias": "my-link",
"expire_at": "2025-04-30T22:30+00:00"
}
```
#### Получение оригинальной ссылки (редирект)
```http
GET /links/{short_id}
```

#### Получение статистики по ссылке
```http
GET /links/{short_id}/stats
```

#### Обновление ссылки
```http
PUT /links/{short_id}

{
"original_url": "https://new-example.com",
"expire_at": "2025-05-30T22:30+00:00"
}
```


#### Удаление ссылки
```http
DELETE /links/{short_id}
```

#### Поиск ссылок
```http
GET /links/search/?original_url=http://example.com
```

## Запуск приложения (Docker Compose)

1. Создать `.env` из шаблона и при необходимости отредактировать значения:
   ```bash
   cp .env.example .env
   ```
2. Поднять контейнеры:
   ```bash
   docker-compose up -d --build
   ```
3. Применить миграции БД:
   ```bash
   docker-compose exec web alembic upgrade head
   ```

Сервис доступен на `http://localhost:8000`. OpenAPI: `http://localhost:8000/docs`.

## Установка для разработки и тестирования

Тесты не требуют запущенного `docker-compose` — они используют SQLite in-memory и mock-Redis (см. `tests/conftest.py`). Для прогона тестов локально достаточно `python` с зависимостями из `requirements.txt` и `requirements-dev.txt`:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Состав dev-зависимостей: `pytest`, `pytest-asyncio`, `httpx`, `pytest-mock`, `coverage`, `locust`.

## Запуск тестов

```bash
pytest tests/             # все тесты
pytest tests/unit/        # только юнит-тесты
pytest tests/functional/  # только функциональные API-тесты
```

Опция `-v` даёт подробный вывод по каждому тесту. Тесты используют SQLite in-memory и mock-Redis — внешние сервисы поднимать не нужно.

## Отчёт покрытия (coverage)

Выполнить четыре команды последовательно из корня форка:

```bash
coverage run -m pytest tests
coverage report
coverage html
rm -f htmlcov/.gitignore
```

`coverage html` версии 7.x автоматически создаёт `htmlcov/.gitignore`, из-за которого git перестаёт видеть содержимое `htmlcov/`. Удаление этого файла оставляет HTML-отчёт видимым в репозитории.

Открыть отчёт в браузере:
- macOS: `open htmlcov/index.html`
- Linux: `xdg-open htmlcov/index.html`
- Windows: `start htmlcov/index.html`

Отчёт уже включён в репозиторий (см. `htmlcov/index.html`) — текущее покрытие **96.96%** при пороге ≥ 90%.

## Нагрузочное тестирование (Locust)

Сценарий — `locustfile.py` в корне форка: один `HttpUser` с двумя задачами (`POST /links/shorten` + `GET /links/{short_id}`) в анонимном профиле и весами 1:3 (на каждый POST приходится в среднем три GET'а).

1. Поднять приложение через docker-compose (см. раздел «Запуск приложения»).
2. В отдельном терминале из корня форка выполнить headless-прогон:
   ```bash
   locust --headless -u 10 -r 2 -t 60s --host http://localhost:8000 -f locustfile.py --html locust_report.html --csv locust_results
   ```

Параметры: `-u 10` — пиковая концурренси 10 пользователей, `-r 2` — спавн 2 пользователя/сек, `-t 60s` — общее время прогона 60 секунд. Артефакты: `locust_report.html` (HTML-отчёт) и `locust_results_stats.csv` (plain-text сводка). Образцовый отчёт прогона уже включён в репозиторий: `locust_report.html` (открыть в браузере).
