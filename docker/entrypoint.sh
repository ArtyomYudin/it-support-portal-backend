#!/bin/bash
set -e

# Получаем Kerberos тикет перед запуском Celery
if [ -z "$KERBEROS_PASSWORD" ]; then
    echo "Ошибка: не задана переменная KERBEROS_PASSWORD"
    exit 1
fi

echo "$KERBEROS_PASSWORD" | kinit "$KERBEROS_USER"

# Запускаем команду переданную в CMD
exec "$@"