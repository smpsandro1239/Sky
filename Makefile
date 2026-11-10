.PHONY: up down logs ps test-api

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f --tail=100

ps:
	docker compose ps

test-api:
	cd apps/api && python -m pytest
