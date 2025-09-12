rabbitmqctl add_vhost it_support --description "IT Support Portal" --default-queue-type quorum

rabbitmqctl add_user pacs_tcp_client "97OUWipH4txB"
rabbitmqctl add_user backend "kMe22aRIN5wi"
rabbitmqctl add_user celery "3bC2Kv4UDrtN"


# First ".*" for configure permission on every entity
# Second ".*" for write permission on every entity
# Third ".*" for read permission on every entity

rabbitmqctl set_permissions -p it_support pacs_tcp_client "pacs.*" "pacs.*" ""
rabbitmqctl set_permissions -p it_support backend ".*" ".*" ".*"
rabbitmqctl set_permissions -p it_support celery ".*" ".*" ".*"

rabbitmqctl list_permissions -p it_support




# Запуск воркера
celery -A core.celery worker --loglevel=info

# Запуск планировщика
celery -A core.celery beat --loglevel=info