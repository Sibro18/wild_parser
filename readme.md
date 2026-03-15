# Wild Parser

Документация по запуску проекта двумя способами:
- через Docker Compose
- **локально**, без Docker

Проект использует:
- Python 3.11
- openpyxl
- aiohttp
- playwright
- ruff

---

# Запуск через Docker Compose

- Шаг 1: **Убедись, что Docker и Docker Compose установлены.**
- Шаг 2: **Запусти Docker на своём устройстве.**
- Шаг 3: **выполни команду `docker-compose up --build`**

# Запуск через с локального устройства

- Шаг 1: **Создай виртуальное окружение: `python -m venv .venv`**
- Шаг 2: **Активируй виртуальное окружение с помощью подходящего скрипта из `.venv\Scripts`**
- Шаг 3: **Установи зависимости: `pip install -r requirements.txt`**
- Шаг 4: **Установи необходимый для playwright драйвер: `playwright install chromium`**
- Шаг 5: **Запустить приложение: `python src/main.py`**
