# Documentation System Design

## Date: 2026-03-08

## Goal

Set up a rendered documentation site for the Bennu project using MkDocs Material,
organized with the Diátaxis framework (Tutorials, How-to, Concepts, Reference)
plus ADRs and a Build Log. Content is extracted from existing docs without
modifying the originals. Auto-deployed to GitHub Pages via GitHub Actions.

## Audience

- Primary: project author (future reference)
- Secondary: open-source community (replication, contribution)

## Tool & Stack

- **MkDocs Material** — Python-based static site generator
- **Mermaid** diagrams — built-in plugin, replaces ASCII art
- **Blog plugin** — for Build Log (chronological journal)
- **GitHub Actions** — auto-deploy to GitHub Pages on push to `main`

## Site Structure

```
docs/
├── index.md                          # Landing page (project overview)
├── tutorials/
│   ├── index.md                      # Tutorials overview
│   └── frame-assembly.md             # From build-guide/01-frame-assembly.md
├── how-to/
│   ├── index.md                      # How-to overview
│   ├── flash-px4-params.md           # From firmware scripts
│   ├── run-simulation.md             # From sim/README.md
│   ├── transfer-images.md            # From ground/transfer workflow
│   └── start-webodm.md              # From ground/odm workflow
├── concepts/
│   ├── index.md                      # Concepts overview
│   ├── system-architecture.md        # From design doc (architecture section)
│   ├── photogrammetry-pipeline.md    # From design doc (pipeline section)
│   └── simulation-stack.md           # From SITL design doc
├── reference/
│   ├── index.md                      # Reference overview
│   ├── bill-of-materials.md          # From design doc (BOM)
│   ├── wiring-diagram.md             # From wiring/wiring-diagram.md
│   ├── frame-specifications.md       # From frame/README.md
│   ├── px4-parameters.md             # From firmware/px4/params
│   └── ros2-interfaces.md            # ROS2 topics/services/params
├── decisions/
│   ├── index.md                      # ADR index + template
│   ├── 001-px4-over-ardupilot.md
│   ├── 002-pi5-companion-computer.md
│   ├── 003-rolling-shutter-camera.md
│   └── 004-uxrce-dds-over-mavros.md
├── blog/
│   ├── index.md                      # Build log landing
│   └── posts/
│       └── .gitkeep                  # Posts added over time
└── plans/                            # UNTOUCHED — existing planning docs
    └── (existing files stay as-is)
```

## Content Sources

Content is **extracted** (copied and enhanced), not moved. Originals stay untouched.

| New Page | Source | What Gets Extracted |
|---|---|---|
| `tutorials/frame-assembly.md` | `build-guide/01-frame-assembly.md` | Full content, enhanced with Mermaid |
| `how-to/run-simulation.md` | `sim/README.md` | Quick start, commands, architecture |
| `how-to/flash-px4-params.md` | `firmware/` scripts + params | Usage instructions |
| `how-to/transfer-images.md` | `ground/transfer/` | Transfer workflow |
| `how-to/start-webodm.md` | `ground/odm/` | WebODM setup + usage |
| `concepts/system-architecture.md` | Design doc | Architecture section, ASCII→Mermaid |
| `concepts/photogrammetry-pipeline.md` | Design doc | Pipeline section |
| `concepts/simulation-stack.md` | SITL design doc | Sim architecture |
| `reference/bill-of-materials.md` | Design doc | BOM tables |
| `reference/wiring-diagram.md` | `wiring/wiring-diagram.md` | Full content, ASCII→Mermaid |
| `reference/frame-specifications.md` | `frame/README.md` | Print specs, parts list |
| `reference/px4-parameters.md` | `firmware/px4/params/*.yaml` | Parameter docs |
| `reference/ros2-interfaces.md` | ROS2 package sources | Topics, services, params |
| `decisions/001-004` | Design doc | Decision rationale extracted |

## ADR Format

Each ADR follows this template:

```markdown
# ADR-NNN: Title

## Status
Accepted | Proposed | Superseded

## Context
Why the decision was needed.

## Decision
What was decided.

## Consequences
Trade-offs and implications.
```

## Mermaid Diagram Upgrades

ASCII diagrams in source docs get converted to Mermaid in new pages:

- System architecture → flowchart
- Wiring / power distribution → flowchart
- Photogrammetry pipeline → sequence diagram
- Simulation stack → container diagram

## Key Config Files

- `mkdocs.yml` — repo root, site configuration
- `.github/workflows/docs.yml` — GitHub Actions deploy workflow
- `requirements-docs.txt` — Python dependencies for MkDocs

## Deployment

- GitHub Actions triggers on push to `main` (changes in `docs/` or `mkdocs.yml`)
- Builds with `mkdocs build`, deploys to `gh-pages` branch
- Served at `https://<user>.github.io/bennu/`

## Existing Docs

The `docs/plans/` directory is **not touched**. These are working artifacts
used by the development workflow and are excluded from the rendered site navigation.
