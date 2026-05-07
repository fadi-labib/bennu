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
   cd sim && make test    # Unit tests
   cd sim && make test-smoke    # SIL integration tests
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

## AI Coding Assistants

Adapted from the [Linux kernel coding assistants policy](https://github.com/torvalds/linux/blob/master/Documentation/process/coding-assistants.rst).

AI tools (Claude, Copilot, ChatGPT, etc.) may be used to assist with contributions. When they are, the following rules apply:

### Human Responsibility

The human submitter is responsible for:

- Reviewing all AI-generated code for correctness and safety
- Ensuring compliance with the project's licensing (Apache-2.0)
- Testing the contribution locally before submitting
- Taking full responsibility for the contribution

AI tools do not have legal standing. A human must stand behind every contribution.

### Attribution

AI tools must NOT be listed as commit author or co-author (`Co-Authored-By` is not permitted for AI tools). Only humans author commits.

When AI tools contribute to development, include an `Assisted-by` trailer in the commit message body:

```
feat: add terrain following for survey waypoints

Implement altitude adjustment using DEM elevation data to maintain
constant AGL over hilly terrain.

Assisted-by: Claude:claude-opus-4-6
```

The format is `Assisted-by: TOOL_NAME:MODEL_VERSION`. This helps track the role of AI in the project's development without misrepresenting authorship.

### What Counts as AI Assistance

Include the `Assisted-by` trailer when an AI tool:

- Generated or substantially wrote code that was committed
- Designed an architecture or algorithm that was implemented
- Debugged an issue by identifying the root cause

Do NOT include it for:

- Using AI for general questions or documentation lookup
- Autocomplete suggestions (IDE-level Copilot completions)
- Spell-checking or grammar fixes

## Code of Conduct

Be respectful. Constructive feedback is welcome; personal attacks are not. Maintainers reserve the right to remove comments or block users who violate this principle.

## Questions?

Open a [discussion](https://github.com/fadi-labib/bennu/discussions) or file an issue. We are happy to help.
