# 🧰 IT Support Portal — Backend

**IT Support Portal Backend** — это серверная часть системы для автоматизации и управления процессами IT-поддержки.  
Приложение реализовано на **FastAPI** с использованием **PostgreSQL**, **Celery**, **RabbitMQ** и **Docker**.

---

## 🚀 Основные возможности

- 👥 Управление пользователями и аутентификация (JWT)
- 🎫 Работа с тикетами и обращениями
- ⚙️ Асинхронные задачи и интеграции через Celery
- 💾 Хранение данных в PostgreSQL
- 📨 Интеграции с почтой (IMAP)
- 🔄 Миграции базы данных с помощью Alembic
- 🐳 Полная контейнеризация через Docker Compose
- 📦 Гибкая конфигурация через `.env`

---

## 🧱 Архитектура проекта
```
├── api/                 # Маршруты и контроллеры API (FastAPI)
├── core/                # Основные настройки приложения
├── db/                  # Подключение к БД, модели и репозитории
├── services/            # Бизнес-логика
├── tasks/               # Фоновые задачи Celery
├── utils/               # Вспомогательные функции
├── alembic/             # Миграции базы данных
├── docker/              # Конфигурация Docker и сервисов
├── rabbitmq/            # Настройки брокера сообщений
├── main.py              # Точка входа API
├── worker.py            # Celery worker
├── requirements.txt     # Зависимости Python
└── .env                 # Переменные окружения
```

---

## ⚙️ Технологический стек

| Компонент | Используемая технология |
|------------|-------------------------|
| Backend Framework | **FastAPI** |
| Database | **PostgreSQL** |
| ORM | **SQLAlchemy (async)** |
| Migrations | **Alembic** |
| Task Queue | **Celery** |
| Message Broker | **RabbitMQ** |
| Auth | **JWT (python-jose, passlib)** |
| Config | **dotenv, pydantic-settings** |
| Containerization | **Docker & Docker Compose** |

---

## 🧩 Установка и запуск

### 1. Клонирование репозитория
```bash
git clone https://github.com/ArtyomYudin/it-support-portal-backend.git
cd it-support-portal-backend
