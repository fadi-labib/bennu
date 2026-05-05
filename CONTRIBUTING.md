# Contributing to Bennu

Thank you for your interest in contributing to Bennu! This document explains how to get involved.

## Reporting Bugs

Open a [GitHub issue](https://github.com/fadi-labib/bennu/issues) with:

- A clear, descriptive title
- Steps to reproduce the problem
- Expected vs. actual behavior
- Your environment (Ubuntu version, ROS2 distro, PX4 version)
- Relevant logs or screenshots

## Submitting Changes

1. **Fork** the repository and create a branch from `main` using a conventional prefix:
   ```bash
   git checkout -b feat/your-feature main
   ```
   | Prefix | Use for |
   |--------|---------|
   | `feat/` | New features |
   | `fix/` | Bug fixes |
   | `docs/` | Documentation only |
   | `chore/` | Maintenance, deps, CI |
   | `refactor/` | Code restructuring |
   | `test/` | Test additions or fixes |

2. **Make your changes.** Follow the code style and conventions below.
3. **Test locally:**
   ```bash
   cd sim && make test-unit    # Unit tests
   cd sim && make test-sitl    # SIL integration tests
   ```
4. **Commit** with a clear message (see commit format below).
5. **Push** your branch and open a pull request against `main`.

## Code Style

- **Linter:** [ruff](https://docs.astral.sh/ruff/) for Python linting and formatting.
- **Tests:** [pytest](https://docs.pytest.org/) for all test suites.
- **Type hints:** Preferred for public function signatures.
- Run `ruff check .` and `ruff format --check .` before submitting.

## ROS2 Conventions

- Package names use the `bennu_*` prefix (e.g., `bennu_camera`, `bennu_bringup`).
- All nodes are written in Python using `rclpy`.
- Launch files live in `bennu_bringup`.
- Node names are descriptive lowercase with underscores (e.g., `camera_capture_node`).

## Commit Message Format

Use imperative mood in the subject line, keep it under 72 characters:

```
feat: add geotag validation for altitude bounds

fix: correct HFOV calculation for 6mm lens

test: add integration test for camera timer parameter
```

Prefix with a type: `feat`, `fix`, `test`, `docs`, `refactor`, `config`, `ci`.

## Code of Conduct

Be respectful. Constructive feedback is welcome; personal attacks are not. Maintainers reserve the right to remove comments or block users who violate this principle.

## Questions?

Open a [discussion](https://github.com/fadi-labib/bennu/discussions) or file an issue. We are happy to help.
