# Bennu — top-level entry point.
#
# Forwards common targets to sim/Makefile so contributors can run
# them from the repo root without `cd sim`. Also exposes a few
# convenience targets for sibling subdirectories (drone/, ground/).
#
# `cd sim && make <target>` still works — this Makefile is purely
# additive.

.PHONY: help sim dev dev-watch dev-debug qgc test test-smoke test-sitl test-all clean ros2-build

help: ## Show available commands
	@echo "Bennu — top-level commands (run from repo root)"
	@echo ""
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# --- Simulation targets (forward to sim/Makefile) -------------------------

sim: ## One-command sim: containers + QGC + auto-fly + shell
	@$(MAKE) -C sim sim

dev: ## Headless: containers only (CI / SSH / no GUI)
	@$(MAKE) -C sim dev

dev-debug: ## Headless + Gazebo GUI (requires GPU + X11)
	@$(MAKE) -C sim dev-debug

dev-watch: ## Dev environment + pytest-watch auto-rerun
	@$(MAKE) -C sim dev-watch

qgc: ## Launch QGroundControl (auto-downloads on first run)
	@$(MAKE) -C sim qgc

test: ## Run unit + contract + integration tests
	@$(MAKE) -C sim test

test-smoke: ## Run SIL smoke test (nominal_survey scenario)
	@$(MAKE) -C sim test-smoke

test-sitl: ## Run all SIL scenario tests
	@$(MAKE) -C sim test-sitl

test-all: ## Run all tests (unit + SIL)
	@$(MAKE) -C sim test-all

clean: ## Stop all sim containers, remove volumes
	@$(MAKE) -C sim clean

# --- Drone (companion computer) targets -----------------------------------

ros2-build: ## Build ROS2 workspace (drone/ros2_ws)
	@cd drone/ros2_ws && colcon build --symlink-install
