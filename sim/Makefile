# Bennu Simulation — Developer Interface
# Usage: cd sim && make <target>
#
# Run `make help` to see all available commands.

.PHONY: dev dev-watch dev-debug test-unit test-sitl test-scenarios test-all clean help

COMPOSE_DEV = docker compose -f docker-compose.dev.yml
COMPOSE_SIL = docker compose -f docker-compose.sil.yml
COMPOSE_DBG = docker compose -f docker-compose.debug.yml
DEV_EXEC    = docker exec bennu-ros2-dev bash -c

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

dev: ## Start dev environment (headless PX4 + ros2-dev shell)
	$(COMPOSE_DEV) up -d
	@echo "Dev environment ready. Run: docker exec -it bennu-ros2-dev bash"

dev-watch: dev ## Start dev + pytest-watch auto-rerun
	@echo "Starting pytest-watch (Ctrl+C to stop)..."
	$(DEV_EXEC) "pip install -e /ros2_ws/src/bennu/* 2>/dev/null; \
		cd /ros2_ws && ptw --runner 'python -m pytest --tb=short -q' src/bennu/*/test/ tests/"

dev-debug: ## Start debug environment with Gazebo GUI (requires GPU + xhost)
	$(COMPOSE_DBG) up -d
	@echo "Debug environment ready with Gazebo GUI."

test-unit: ## Run unit + contract + integration tests (starts PX4 via depends_on)
	$(COMPOSE_DEV) up -d ros2-dev
	$(DEV_EXEC) "cd /ros2_ws && pip install -e src/bennu/* 2>/dev/null && \
		python -m pytest src/bennu/*/test/ tests/ -v"

test-sitl: ## Run full mission SIL headless
	$(COMPOSE_SIL) up --build --abort-on-container-exit --exit-code-from test-runner
	$(COMPOSE_SIL) down -v

test-scenarios: ## Run scenario matrix
	$(COMPOSE_SIL) run --rm test-runner \
		python3 /ros2_ws/scripts/run_scenarios.py --dir /ros2_ws/scenarios/

test-all: test-unit ## Run unit + sitl tests
	$(COMPOSE_DEV) down -v 2>/dev/null || true
	$(MAKE) test-sitl

clean: ## Stop all containers, remove volumes
	$(COMPOSE_DEV) down -v 2>/dev/null || true
	$(COMPOSE_SIL) down -v 2>/dev/null || true
	$(COMPOSE_DBG) down -v 2>/dev/null || true
