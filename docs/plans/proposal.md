# Proposal: Bennu Drone + Independent OSS Geospatial Platform

**Date:** 2026-03-08  
**Status:** Proposed  
**Decision Type:** Strategic + Technical

## 1) Vision

Build a production-grade, open, vendor-neutral system for aerial monitoring where:

- **Bennu (this repo)** is a reliable data-acquisition drone stack.
- **Platform (separate repo)** is the analysis, mapping, and decision system.
- Both are loosely coupled through a versioned data contract.

This avoids lock-in, enables self-hosted deployments, and supports multiple domains
(agriculture, infrastructure, environment, construction, asset inspection).

## 2) Strategic Lessons Incorporated

From Mavic 3M-style workflows, we adopt:

1. The pipeline is the product (`plan -> fly -> capture -> process -> analyze -> act`).
2. Calibrated measurements matter more than raw imagery.
3. RTK/geo-quality is foundational for repeatable monitoring.
4. Mission repeatability (same footprint, overlap, GSD) is essential.
5. Closed-loop outputs must become next-mission inputs.

## 3) Boundaries (Critical)

### Drone Project (this repository)

Owns:

- flight stack, onboard capture, mission execution
- sensor integration and capture metadata
- mission bundle export (offline-first)
- local QA tooling (optional processing checks)

Does not own:

- multi-tenant backend platform
- long-term catalog/database services
- dashboards, enterprise API gateway, user management

### Platform Project (separate repository)

Owns:

- ingestion, storage, STAC/catalog, APIs, analytics UI
- workflow orchestration, model lifecycle, alerting
- auth/RBAC/audit/SLO operations

## 4) Drone-to-Platform Contract (Mandatory First Deliverable)

Define and freeze a versioned mission bundle contract:

- `images/*.jpg`
- `metadata/mission.json`
- `metadata/images.csv`
- `checksums.sha256`
- `contract_version`

Rules:

- semantic versioning (`v1`, `v1.1`, `v2`)
- strict schema validation in CI
- backward-compatibility policy and migration notes

## 5) Workstreams

### A) Bennu Drone Workstream (this repo)

1. Data contract + exporter (contract-first).
2. Capture quality gates:
   - blur threshold
   - exposure checks
   - overlap/coverage checks
   - geotag completeness
   - RTK fix status recording
3. Hardware upgrades (priority order):
   - RTK GPS (F9P class)
   - multispectral path (realistic band strategy)
   - radiometric calibration workflow (panel and/or calibrated irradiance path)
   - terrain-following sensor stack suitable for outdoor AGL use
4. Survey intelligence packages:
   - `bennu_survey` (grid planning, repeat missions, terrain-aware planning)
   - `bennu_mission` enhancements (execution + manifest generation)
5. Production hygiene:
   - compatibility matrix (PX4/ROS2/px4_msgs/XRCE)
   - pinned dependencies
   - CI pipelines (lint/test/smoke)
   - runbooks + incident checklist

### B) Platform Workstream (separate repo)

1. Core services:
   - object storage
   - PostGIS + STAC catalog
   - API + worker orchestration
2. Processing:
   - preprocessing + inference + postprocess pipelines
3. Product surface:
   - map UI, change detection, alerting
4. Production controls:
   - RBAC, audit logs, observability, backup/restore, SLO dashboards

### C) Integration Workstream

1. Publish adapters from drone bundles (`local`, `s3`, `http`).
2. Integration tests: bundle export -> ingestion -> query -> analytics artifact.
3. Contract conformance tests on both repos.

## 6) Phase Plan and Exit Gates

## Phase 0 (1-2 weeks): Foundation and Governance

Deliverables:

- contract spec document
- compatibility matrix
- CI baseline
- project governance files (`LICENSE`, `CONTRIBUTING`, `SECURITY`, `CODEOWNERS`)

Exit gates:

- CI required for merges
- contract validator passing
- pinned critical dependencies

## Phase 1 (2-3 weeks): Data Quality Baseline

Deliverables:

- RTK integration
- capture metadata enrichment
- quality-gate checks in capture/export path

Exit gates:

- >= 99% images with complete metadata fields
- RTK fix quality logged for all missions
- deterministic mission bundle export

## Phase 2 (2-4 weeks): Multispectral + Calibration

Deliverables:

- dual-sensor capture path
- calibration workflow and docs
- repeat-flight validation procedure

Exit gates:

- reproducible index maps across repeated flights within defined tolerance
- calibration artifacts stored per mission

## Phase 3 (3-4 weeks): Survey Intelligence

Deliverables:

- grid planner + site registry
- repeat mission support
- terrain-aware planning path

Exit gates:

- mission replay on same AOI with bounded path deviation
- coverage targets met for configured overlap profile

## Phase 4 (parallel, 90 days): Platform v1

Deliverables:

- ingestion/catalog/API/pipeline/ui stack
- auth/audit/observability/recovery runbooks

Exit gates:

- end-to-end ingestion and analytics flow in staging
- SLO dashboards + alert routing active

## 7) Success Metrics

- data package reliability: >= 99% successful bundle generation
- metadata completeness: >= 99% required fields present
- mission repeatability: bounded overlap/GSD variance against profile targets
- integration reliability: >= 99% successful ingest from valid bundles
- operational readiness: documented restore drill and incident runbook exercised

## 8) Risks and Mitigations

1. **Over-optimistic sensor assumptions**  
Mitigation: validate sensors in controlled tests before committing architecture.

2. **Scope creep across drone + platform**  
Mitigation: enforce repo boundaries and contract-based integration.

3. **Version drift and fragile reproducibility**  
Mitigation: pinned dependencies + compatibility matrix + release notes.

4. **Production claims without ops maturity**  
Mitigation: SLOs, runbooks, backups, and CI gates required before “prod” label.

## 9) Recommendation

Approve this proposal with a **contract-first execution**:

1. finalize Phase 0 artifacts in this repo
2. implement drone quality pipeline (Phases 1-3)
3. run platform build in parallel using the exported contract

This gives Bennu a practical path from photogrammetry prototype to production-grade
open system without coupling drone firmware decisions to platform architecture.
