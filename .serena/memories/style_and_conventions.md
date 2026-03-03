# Code Style & Conventions

## Python
- **Style:** Standard Python, no strict linter enforced yet (ruff available in container)
- **Type hints:** Not consistently used — not required
- **Docstrings:** Minimal, only where logic isn't self-evident
- **Naming:** lowercase_snake_case for functions/variables, PascalCase for classes
- **Imports:** Standard library first, then third-party, then local

## ROS2 Conventions
- Package names: `bennu_*`
- Use `rclpy` (Python) for all nodes
- Launch files in `bennu_bringup`
- Node names: descriptive lowercase (e.g., `camera_capture_node`)
- Parameters: declared via `self.declare_parameter()`

## Git Conventions
- Conventional commits: `feat:`, `fix:`, `chore:`, `docs:`, `ci:`
- Scoped commits: `feat(sim):`, `fix(sim):` for simulation work
- **NEVER include Co-Authored-By Claude in commit messages**
- Commit and push after every task

## Workflow Rules
- When a plan is completed: convert to ADR/design doc/mkdocs page, then delete the plan file
- Completed plans should not linger in `docs/plans/`
