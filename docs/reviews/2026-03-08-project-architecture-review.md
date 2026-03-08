# Bennu Project Review and Follow-up Plan

**Date:** 2026-03-08  
**Scope:** Consolidated review of architecture, design choices, dependency strategy, plan quality, and scaffold implementation risks.

## 1) Executive Summary

The project direction is strong for an R&D photogrammetry platform, but the current state is **scaffold-grade**, not production-grade.

- **Architecture intent:** strong (clear split between flight-critical and non-flight-critical compute)
- **Design maturity:** medium (good concept, incomplete systems engineering artifacts)
- **Dependency governance:** weak-to-medium (version drift, pinning gaps)
- **Operational readiness:** low (several high-severity risks still unresolved)

## 2) What Is Strong

- Correct high-level separation:
  - PX4 on Pixhawk for flight-critical control.
  - Companion computer for camera/data/autonomy logic.
  - Ground station for mission planning and photogrammetry processing.
- Good stack choices for long-term autonomy:
  - PX4 + ROS2 + uXRCE-DDS instead of MAVROS bridge complexity.
- Sensible phased delivery model:
  - Fly first, then survey, then autonomy.
- SITL early in lifecycle is the right call for safer iteration.
- Repo structure is generally clear and deployment-target oriented (`drone/`, `firmware/`, `ground/`, `sim/`, `docs/`).

## 3) Consolidated Findings

### A. Critical / High-Risk Findings

1. **Datalink failsafe misconfiguration**
   - `NAV_DLL_ACT: 0` is commented as RTL but value `0` is effectively disabled in PX4 param semantics.
   - Impact: potential unsafe behavior on datalink loss.

2. **Sim architecture conflict (double XRCE agent)**
   - Agent started in container default command and again via launch in sim workflow.
   - Impact: port/channel conflict, nondeterministic startup behavior.

3. **`bennu_camera` packaging is not fully `ament_python`-compliant**
   - Missing expected install metadata/resource marker in setup packaging path.
   - Impact: package discovery/deployment fragility.

4. **Agent binary naming mismatch across environments**
   - Setup references `micro-xrce-dds-agent`; launch uses `MicroXRCEAgent`.
   - Impact: startup failures depending on install source.

5. **PX4 parameter uploader design is fragile**
   - Reopens MAVLink session per parameter, coerces all values as float, weak ack verification.
   - Impact: silent misconfiguration risk.

6. **ODM processing script exits on empty image folder**
   - Current shell behavior can fail before graceful handling.
   - Impact: brittle operations and confusing failure mode.

### B. Architecture / Systems-Engineering Gaps

7. **Too many high-risk fronts changed simultaneously**
   - Custom frame + custom companion stack + photogrammetry pipeline + sim environment.
   - Impact: integration burden and slower root-cause isolation.

8. **Airframe strategy risk for mapping quality**
   - Heavy reliance on printed structure can increase vibration/camera instability risk.
   - Impact: degraded image sharpness and reconstruction quality.

9. **Geospatial accuracy strategy incomplete**
   - No explicit RTK/PPK/GCP strategy in base architecture.
   - Impact: limited absolute accuracy for professional survey outputs.

10. **Power architecture underspecified for Pi 5 reliability**
    - BEC margin/thermal/noise treatment not fully specified.
    - Impact: brownouts, unstable compute node, image/data loss.

11. **Ops/observability architecture is thin**
    - No explicit health checks, fault telemetry conventions, retention strategy.
    - Impact: difficult debugging and weak field reliability.

### C. Dependency / Planning / Governance Gaps

12. **Version drift across docs and implementation**
    - Inconsistent references around ROS distro and PX4 versioning.
    - Impact: non-reproducible setup and onboarding confusion.

13. **Weak dependency pinning policy**
    - Floating branches/tags/images in critical paths.
    - Impact: hidden breakage over time.

14. **Plan lacks enforceable acceptance gates**
    - No formal go/no-go criteria per phase.
    - Impact: phase progression without objective quality threshold.

15. **Missing core systems artifacts**
    - No concise, measurable requirements baseline.
    - No safety/hazard register.
    - No compatibility matrix.
    - No verification matrix linking requirements to tests.

16. **Testing and CI baseline is minimal**
    - Small unit-test footprint, no automated CI guardrails.
    - Impact: regressions can slip through unnoticed.

17. **Roadmap-to-repo mismatch**
    - Some planned assets/workspaces remain placeholders.
    - Impact: architecture claims exceed implemented baseline.

## 4) Consolidated Proposals

### Immediate Corrections (Safety and Determinism)

1. Fix failsafe configuration semantics and comments (especially datalink-loss behavior).
2. Enforce **single XRCE agent authority** per transport/channel in sim and real modes.
3. Standardize one supported agent binary invocation strategy across all environments.
4. Harden parameter upload mechanism (single session, typed values, strict ack checks).
5. Make core operational scripts robust (empty-input handling, clear exit codes, actionable logs).

### Architecture Hardening

6. Add a formal requirements baseline with measurable targets:
   - Endurance, GSD, overlap, reconstruction quality thresholds, mission completion rate.
7. Add safety/hazard register with mitigations and go/no-go checklists.
8. Add power and mass budgets with margins and thermal/noise assumptions.
9. Add geospatial accuracy strategy:
   - Define baseline absolute accuracy and upgrade path (RTK/PPK/GCP).
10. Add observability design:
   - Health/status topics, fault classes, logging retention, post-flight artifacts.

### Dependency Governance

11. Publish a compatibility matrix (PX4, `px4_msgs`, ROS2 distro, agent version, Docker tags).
12. Pin critical dependencies to known-good versions and track upgrade cadence.
13. Remove ambiguous “latest” usage in critical runtime paths where reproducibility matters.

### Process and Quality

14. Add CI for lint/tests/smoke checks (including launch/sim smoke tests).
15. Add phase gates with explicit pass/fail criteria before advancing roadmap phases.
16. Add requirement-to-test traceability matrix.

## 5) Follow-up Execution Plan (Actionable Roadmap)

## Phase 0: Stabilize Foundation (1 week)

**Goal:** eliminate safety/config nondeterminism and align dependency story.

Tasks:
- Correct failsafe parameters and comments.
- Resolve XRCE single-agent architecture in sim and docs.
- Normalize agent command usage across setup/launch/container.
- Create compatibility matrix and pin versions.
- Fix brittle scripts for deterministic behavior.

Exit criteria:
- Single documented startup path works in sim.
- Safety-critical params reviewed and signed off.
- Compatibility matrix exists and is referenced from root docs.

## Phase 1: Systems Baseline Artifacts (1 week)

**Goal:** convert scaffold into an engineering-controlled project.

Tasks:
- Author `System Requirements` document.
- Author `Safety & Hazard Register`.
- Author `Power Budget` and `Mass Budget`.
- Author `Validation Plan` with measurable criteria.

Exit criteria:
- Each requirement has a measurable metric and target.
- Each major hazard has mitigation and verification method.

## Phase 2: Verification Infrastructure (1 week)

**Goal:** prevent regressions and increase confidence.

Tasks:
- Add CI pipeline (lint + unit tests + shell checks + sim smoke test).
- Expand test coverage around camera/geotagging and scripts.
- Add requirement-to-test traceability table.

Exit criteria:
- CI required for merges.
- Smoke test validates basic bringup path.

## Phase 3: Mapping Quality and Accuracy Plan (1-2 weeks)

**Goal:** ensure architecture can actually deliver usable survey outputs.

Tasks:
- Define camera vibration acceptance metrics (blur rejection criteria).
- Define mission profile defaults for overlap/speed/altitude.
- Define geospatial accuracy path (baseline + RTK/PPK/GCP optional track).

Exit criteria:
- Documented quality KPIs for dataset acceptance.
- Accuracy expectations declared before field flights.

## Phase 4: Operational Maturity (ongoing)

**Goal:** make field operations repeatable and diagnosable.

Tasks:
- Add runbooks (pre-flight, in-flight monitoring, post-flight data handling).
- Add logs/health conventions and fault handling SOP.
- Add maintenance/release cadence for dependency upgrades.

Exit criteria:
- Repeatable operation checklist used in every flight.
- Issues are diagnosable from captured logs/artifacts.

## 6) Priority Queue (Strict Order)

1. Failsafe semantics correction and review.
2. XRCE single-agent architecture cleanup.
3. Compatibility matrix + version pinning.
4. Script hardening (`param upload`, `ODM process`, `transfer`).
5. Requirements + safety + validation artifacts.
6. CI and traceability.
7. Mapping accuracy and quality strategy.

## 7) Tracking Template (Use for Each Task)

For every task, track:
- **Owner**
- **Due date**
- **Dependencies**
- **Definition of done**
- **Evidence artifact** (test output, log, doc link, screenshot)
- **Risk if skipped**

## 8) Bottom Line

The architecture concept is good and worth continuing.  
To make the foundation “top notch,” prioritize safety determinism, version governance, and systems-engineering artifacts before feature expansion.
