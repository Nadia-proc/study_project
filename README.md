# Russian Verb Trainer

Тренажёр спряжения русских глаголов в настоящем времени для иностранных студентов начального уровня (A1). Сервис на FastAPI.

Сервис выдаёт задания «глагол + лицо» (*читать / ты*) и даёт на каждое несколько попыток. При ошибке подсказывает, что не так: окончание или основа. В конце показывает счёт и разбор ошибок. Регистр, лишние пробелы, ударение, «е» вместо «ё» и местоимение («ты читаешь») ошибкой не считаются.

## Структура

```
app_final.py              # точка входа (uvicorn app_final:app)
conjugator/
  main.py                 # сборка приложения: маршруты, логи запросов, обработка ошибок
  config.py               # настройки из переменных окружения
  dictionary.py           # словарь глаголов (data/verbs.json)
  checker.py              # проверка ответа и подсказки
  sessions.py             # тренировки: задания, попытки, баллы (в памяти)
  schemas.py              # формат запросов и ответов API
  routers/                # маршруты: service, verbs, training
test_app.py               # тесты API
tests/test_logic.py       # тесты логики
.github/workflows/ci.yml  # CI
```

## Установка

Нужен Python 3.10+.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux / macOS
pip install -r requirements-dev.txt
```

## Запуск

```bash
uvicorn app_final:app --host 127.0.0.1 --port 8000
```

Это режим обычной работы. Для разработки добавьте `--reload`, для настроек из файла — `--env-file .env`.

Документация и проверка маршрутов: http://127.0.0.1:8000/docs

## Переменные окружения

Все переменные необязательны. Шаблон лежит в `.env.example`: `cp .env.example .env`. Файл `.env` в git не попадает.

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `LOG_LEVEL` | `INFO` | Уровень логов |
| `MAX_ATTEMPTS` | `3` | Попыток на задание |
| `TASKS_PER_SESSION` | `10` | Заданий в тренировке |
| `MAX_SESSIONS` | `1000` | Тренировок в памяти, старые удаляются |
| `ACCEPT_E_FOR_YO` | `true` | Засчитывать «е» вместо «ё» |
| `RANDOM_SEED` | — | Фиксирует набор заданий |

## Маршруты

| Метод | Путь | Описание |
|---|---|---|
| GET | `/health`, `/version` | Состояние и версия сервиса |
| GET | `/verbs` | Список глаголов |
| GET | `/verbs/{infinitive}` | Спряжение глагола |
| POST | `/sessions` | Начать тренировку, тело необязательно: `{"tasks": 5}` |
| GET | `/sessions/{id}` | Текущее задание и счёт |
| POST | `/sessions/{id}/answer` | Ответ: `{"answer": "читаешь"}` |
| GET | `/sessions/{id}/result` | Итог и разбор ошибок |

Пример тренировки. Проще всего пройти её в `/docs`. В PowerShell вместо `curl` пишите `curl.exe`.

```bash
curl -X POST http://127.0.0.1:8000/sessions -H "Content-Type: application/json" -d '{"tasks": 3}'
# {"session_id": "3f2a...", "task": {"infinitive": "говорить", "person": "ты", "attempts_left": 3, ...}}

curl -X POST http://127.0.0.1:8000/sessions/3f2a.../answer -H "Content-Type: application/json" -d '{"answer": "говорешь"}'
# {"outcome": "incorrect", "hint": "Основа верная, проверь окончание: ... окончание -ишь.", ...}

curl http://127.0.0.1:8000/sessions/3f2a.../result
```

## Тесты

```bash
python -m pytest -v
```

Тесты проверяют `/health` и `/version`, справочник глаголов, полную тренировку, подсказки и исчерпание попыток, ошибки 400/404/422, нормализацию ответов и чтение настроек.

**CI** (GitHub Actions) запускается на каждый push и pull request:
1. ставит зависимости;
2. запускает тесты;
3. поднимает сервер и проверяет `/health` и `/version`;
4. при успехе сохраняет artifact `verb-trainer-app` с файлами приложения (раздел **Artifacts** на странице запуска).

## Диагностика

```bash
curl http://127.0.0.1:8000/health    # {"status": "ok", "verbs_loaded": 21, "active_sessions": 0}
curl http://127.0.0.1:8000/version   # {"name": "Russian Verb Trainer", "version": "1.0.0"}
```

`verbs_loaded > 0` значит, что словарь загрузился. `active_sessions` — число тренировок в памяти.

**Логи** выводятся в консоль, где запущен uvicorn: старт сервиса, каждый запрос, события тренировок и ошибки. Больше деталей даёт `LOG_LEVEL=DEBUG`, сохранить логи в файл можно через `> app.log 2>&1`.

```
2026-10-20 14:00:01 | INFO | conjugator.main | Starting Russian Verb Trainer v1.0.0: 21 verbs loaded, ...
2026-10-20 14:00:09 | INFO | conjugator.sessions | Session 3f2a... answer: говорить/ты -> incorrect
```

| Проблема | Решение |
|---|---|
| `activate`: «выполнение сценариев отключено» | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| `No module named 'fastapi'` | Активируйте `.venv` и установите зависимости |
| `Could not import module "app_final"` | Запускайте из корня проекта |
| `ConfigError: ...` | Исправьте значение переменной в `.env` |
| Порт 8000 занят | `--port 8001` |
| Тренировка не найдена (404) | Тренировки хранятся в памяти и сбрасываются при перезапуске |
