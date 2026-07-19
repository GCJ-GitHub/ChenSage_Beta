PYTHON ?= python3
DOCKER_COMPOSE ?= docker compose
DOCKER_COMPOSE_FILE ?= infra/docker/docker-compose.yml

.PHONY: help setup-env setup-python infra-up infra-down infra-ps migrate-task-svc migrate-knowledge-base-svc test-task-svc test-model-svc test-agent-svc test-eval-svc test-knowledge-base-svc test-agent-worker check-stage0 check-stage1 compile-services run-gateway run-task-svc run-model-svc run-agent-svc run-eval-svc run-knowledge-base-svc run-agent-worker dev-task-svc dev-model-svc dev-agent-svc dev-eval-svc dev-knowledge-base-svc dev-agent-worker dev-stage1

help:
	@echo "ChenSage AgentOS development commands"
	@echo "  make setup-env        Copy local env examples if missing"
	@echo "  make setup-python     Install Python runtime and dev dependencies"
	@echo "  make infra-up         Start PostgreSQL, RabbitMQ, Redis and MinIO"
	@echo "  make migrate-task-svc Run task-svc Alembic migrations"
	@echo "  make migrate-knowledge-base-svc Run knowledge-base-svc Alembic migrations"
	@echo "  make test-task-svc    Run task-svc API and PostgreSQL store tests"
	@echo "  make test-model-svc   Run model-svc provider config and generation tests"
	@echo "  make test-agent-svc   Run agent-svc orchestrator tests"
	@echo "  make test-eval-svc    Run eval-svc evaluation report tests"
	@echo "  make test-knowledge-base-svc Run knowledge-base-svc API tests"
	@echo "  make test-agent-worker Run agent-worker boundary tests"
	@echo "  make check-stage1     Run current local stack checks"
	@echo "  make dev-stage1       Start infra, migrate and local phase 1-7 services"
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

migrate-task-svc:
	$(PYTHON) -m alembic -c services/task-svc/alembic.ini upgrade head

migrate-knowledge-base-svc:
	$(PYTHON) -m alembic -c services/knowledge-base-svc/alembic.ini upgrade head

test-task-svc:
	$(PYTHON) -m pytest services/task-svc/tests

test-model-svc:
	$(PYTHON) -m pytest services/model-svc/tests

test-agent-svc:
	$(PYTHON) -m pytest services/agent-svc/tests

test-eval-svc:
	$(PYTHON) -m pytest services/eval-svc/tests

test-knowledge-base-svc:
	$(PYTHON) -m pytest services/knowledge-base-svc/tests

test-agent-worker:
	$(PYTHON) -m pytest workers/agent-worker/tests

check-stage0:
	$(PYTHON) scripts/check_stage0.py

check-stage1: check-stage0 migrate-task-svc migrate-knowledge-base-svc test-task-svc test-model-svc test-agent-svc test-eval-svc test-knowledge-base-svc test-agent-worker compile-services

compile-services:
	$(PYTHON) -m compileall services workers packages scripts

run-gateway:
	uvicorn app.main:app --app-dir services/gateway --host 0.0.0.0 --port 8000 --reload

run-task-svc:
	uvicorn app.main:app --app-dir services/task-svc --host 0.0.0.0 --port 8011 --reload

dev-task-svc: run-task-svc

run-model-svc:
	uvicorn app.main:app --app-dir services/model-svc --host 0.0.0.0 --port 8012 --reload

dev-model-svc: run-model-svc

run-agent-svc:
	uvicorn app.main:app --app-dir services/agent-svc --host 0.0.0.0 --port 8013 --reload

dev-agent-svc: run-agent-svc

run-eval-svc:
	uvicorn app.main:app --app-dir services/eval-svc --host 0.0.0.0 --port 8015 --reload

dev-eval-svc: run-eval-svc

run-knowledge-base-svc:
	uvicorn app.main:app --app-dir services/knowledge-base-svc --host 0.0.0.0 --port 8014 --reload

dev-knowledge-base-svc: run-knowledge-base-svc

run-agent-worker:
	$(PYTHON) workers/agent-worker/app/main.py

dev-agent-worker: run-agent-worker

dev-stage1:
	$(PYTHON) scripts/dev_stage1.py
