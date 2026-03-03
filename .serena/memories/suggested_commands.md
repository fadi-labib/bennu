# Suggested Commands

## Simulation (run from `sim/` directory)
- `make dev` — Start headless PX4 SITL + ROS2 dev shell
- `make dev-watch` — Start dev + pytest-watch auto-rerun
- `make dev-debug` — Start Gazebo GUI (requires NVIDIA GPU + xhost)
- `make test-unit` — Run unit/contract/integration tests (no PX4)
- `make test-sitl` — Full mission SIL headless
- `make test-sitl BUILD=1` — SIL with local image rebuild
- `make test-all` — Unit + SIL tests
- `make clean` — Stop all containers, remove volumes
- `make help` — List all targets

## ROS2
- `cd drone/ros2_ws && colcon build` — Build ROS2 workspace
- `docker exec -it bennu-ros2-dev bash` — Shell into ROS2 container
- `ros2 launch bennu_bringup drone.launch.py use_sim:=true` — Launch in sim mode

## Ground Station
- `cd ground/odm && docker compose up -d` — Start WebODM
- `./ground/transfer/sync_images.sh` — Transfer images from drone

## Firmware
- `./firmware/px4/upload_params.sh` — Flash PX4 parameters

## Documentation
- `mkdocs serve` — Local docs preview (from repo root, needs .venv activated)

## Git / System
- `git`, `ls`, `cd`, `grep`, `find` — Standard Linux utilities
- `gh pr list`, `gh pr create`, `gh run list` — GitHub CLI
