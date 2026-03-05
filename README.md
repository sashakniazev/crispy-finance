миграции 
alembic init migrations
docker compose exec app alembic revision --autogenerate -m "init"
docker compose exec app alembic upgrade head
docker compose exec app alembic downgrade -1


docker compose up --build 