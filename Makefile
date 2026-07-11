PYTHON ?= python3
DOCKER_COMPOSE ?= docker compose
DOCKER_COMPOSE_FILE ?= infra/docker/docker-compose.yml

.PHONY: help setup-env setup-python infra-up infra-down infra-ps check-stage0 compile-services run-gateway run-task-svc run-model-svc run-agent-svc run-agent-worker

help:
	@echo "ChenSage AgentOS development commands"
	@echo "  make setup-env        Copy local env examples if missing"
	@echo "  make setup-python     Install Python runtime and dev dependencies"
	@echo "  make infra-up         Start PostgreSQL, RabbitMQ, Redis and MinIO"
	@echo "  make infra-down       Stop local infrastructure"
	@echo "  make infra-ps         Show local infrastructure status"
	@echo "  make check-stage0     Verify phase 0 project skeleton"
	@echo "  make compile-services Compile Python service and package skeletons"

setup-env:
	@test -f .env || cp .env.example .env
	@test -f infra/docker/.env || cp infra/docker/.env.example infra/docker/.env

setup-python:
	$(PYTHON) -m pip install -e ".[dev]"

infra-up:
	$(DOCKER_COMPOSE) --env-file infra/docker/.env -f $(DOCKER_COMPOSE_FILE) up -d

infra-down:
	$(DOCKER_COMPOSE) --env-file infra/docker/.env -f $(DOCKER_COMPOSE_FILE) down

infra-ps:
	$(DOCKER_COMPOSE) --env-file infra/docker/.env -f $(DOCKER_COMPOSE_FILE) ps

check-stage0:
	$(PYTHON) scripts/check_stage0.py

compile-services:
	$(PYTHON) -m compileall services workers packages scripts

run-gateway:
	uvicorn app.main:app --app-dir services/gateway --host 0.0.0.0 --port 8000 --reload

run-task-svc:
	uvicorn app.main:app --app-dir services/task-svc --host 0.0.0.0 --port 8011 --reload

run-model-svc:
	uvicorn app.main:app --app-dir services/model-svc --host 0.0.0.0 --port 8012 --reload

run-agent-svc:
	uvicorn app.main:app --app-dir services/agent-svc --host 0.0.0.0 --port 8013 --reload

run-agent-worker:
	$(PYTHON) workers/agent-worker/app/main.py
