#!/bin/bash
set -e

echo ">>> Удаляем все миграции..."
rm -rf migrations/versions/*

echo ">>> Откатываем БД к base (если возможно)..."
alembic downgrade base || echo ">>> alembic_version уже отсутствует"

echo ">>> Чистим таблицу alembic_version (если существует)..."
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "DROP TABLE IF EXISTS alembic_version;"

echo ">>> Создаём новую initial миграцию..."
alembic revision --autogenerate -m "initial"

echo ">>> Применяем миграции..."
alembic upgrade head

echo ">>> Готово. База и миграции пересозданы с нуля."



# 1. Удаляем старые файлы миграций
rm -rf migrations/versions/*

# 2. Сбрасываем указатель Alembic в БД
alembic stamp base

# 3. Генерируем новую миграцию (убедившись, что модели импортированы в env.py!)
alembic revision --autogenerate -m "Initial migration"

# 4. Применяем миграцию
alembic upgrade head