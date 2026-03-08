# Drone/Satellite Image Analysis OSS Platform Plan

**Date:** 2026-03-08
**Status:** Superseded by `2026-03-08-drone-platform-readiness-design.md` — platform moved to separate repo per proposal

## Goal

Define a production-grade open-source platform for drone/satellite image analysis,
independent of a single vertical application (agriculture, infrastructure, security, etc.).

## Scope

This plan covers:

- ingestion of aerial/satellite imagery
- geospatial metadata indexing and search
- preprocessing and ML inference pipelines
- APIs and visualization for analysis outputs
- production operations (security, observability, CI/CD, reliability)

This plan does not cover:

- building a custom flight stack
- a specific downstream domain model (for example crop disease taxonomy)

## Architecture (Production Baseline)

```
Imagery Sources (Drone, Satellite APIs, Manual Upload)
                    |
                    v
          Ingestion + Validation Layer
                    |
                    v
      Object Storage (raw/processed/versioned)
                    |
                    v
   Workflow Orchestrator (scheduled + event-driven jobs)
                    |
        +-----------+-----------+
        |                       |
        v                       v
 Preprocessing Pipeline     ML Inference Pipeline
 (tiling, reprojection,     (segmentation/detection/change)
  cloud mask, QA checks)
        |                       |
        +-----------+-----------+
                    |
                    v
     Spatial DB + Metadata Catalog (PostGIS + STAC)
                    |
                    v
         API Layer + Web Map + Alerting
                    |
                    v
         Monitoring, Audit, SLO Reporting
```

## Recommended OSS Stack

### Core Platform

- **Language/runtime:** Python 3.11+, optional Go for high-throughput services
- **Containerization:** Docker + Docker Compose (early), Kubernetes (scale stage)
- **API:** FastAPI + Pydantic
- **AuthN/AuthZ:** Keycloak or OIDC provider + RBAC

### Geospatial Data

- **Object store:** MinIO (S3-compatible) or AWS S3
- **Spatial DB:** PostgreSQL + PostGIS
- **Raster processing:** GDAL, Rasterio, rio-tiler
- **Array compute:** xarray, dask (if large-batch scale)
- **Catalog standard:** STAC (PySTAC + stac-fastapi)

### ML and Pipelines

- **Training/inference:** PyTorch
- **Experiment/model tracking:** MLflow
- **Workflow orchestration:** Prefect or Airflow
- **Distributed queue (optional):** Celery + Redis

### Visualization and Ops

- **Map UI:** MapLibre GL JS + backend tile endpoints
- **Metrics:** Prometheus + Grafana
- **Logs:** Loki (or ELK)
- **Tracing:** OpenTelemetry
- **Alerts:** Alertmanager

## What Is Core vs Optional

### Core (Day 1)

- object storage
- PostGIS metadata index
- ingestion + validation service
- preprocessing + inference batch pipelines
- API for job submission and result retrieval
- observability baseline (metrics/logs/traces)
- CI/CD and automated tests

### Optional (Depends on Product)

- real-time stream bus (Kafka/MQTT)
- edge inference on drone hardware
- Kubernetes autoscaling from day 1
- multi-tenant billing/subscription layers

## Repository Blueprint

```text
bennu/
├── platform/
│   ├── api/                      # FastAPI: jobs, datasets, outputs
│   ├── ingestion/                # Source connectors + validators
│   ├── pipelines/
│   │   ├── preprocessing/        # GDAL/raster transforms
│   │   ├── inference/            # model runners
│   │   └── postprocess/          # vectorization, summaries
│   ├── catalog/                  # STAC + metadata sync
│   ├── workers/                  # async workers / queue consumers
│   └── common/                   # shared schemas, config, utils
├── ml/
│   ├── datasets/                 # dataset manifests + splits
│   ├── training/                 # training scripts
│   ├── evaluation/               # metrics and validation tools
│   └── models/                   # model definitions
├── infra/
│   ├── compose/                  # local stack
│   ├── k8s/                      # manifests/helm for production
│   ├── terraform/                # cloud provisioning
│   └── observability/            # prom/grafana/loki configs
├── web/
│   └── map-console/              # map UI and analyst workflows
├── docs/
│   ├── architecture/
│   ├── runbooks/
│   ├── security/
│   └── plans/
└── .github/workflows/            # CI, tests, security scans, releases
```

## Data and API Contracts

- Dataset entity:
  `dataset_id`, `source`, `capture_time`, `bbox`, `crs`, `resolution`, `bands`,
  `storage_uri`, `checksum`, `quality_flags`
- Processing job entity:
  `job_id`, `dataset_id`, `pipeline_version`, `model_version`, `status`,
  `started_at`, `finished_at`, `artifacts_uri`
- API principles:
  - versioned endpoints (`/v1/...`)
  - idempotent ingestion (`checksum` + source key)
  - async jobs with polling + webhook callback option

## Reliability and Security Baseline

- **SLOs:** API availability >= 99.5%, batch success rate >= 99%
- **Backups:** daily DB snapshots, object-store versioning
- **Disaster recovery:** documented restore drills each quarter
- **Security controls:** signed container images, dependency scanning, secret manager
- **Auditability:** immutable job/event logs and model version lineage
- **Privacy/legal:** configurable retention and redaction workflows for sensitive imagery

## Quality Gates (Production Grade)

- unit tests for core libraries
- integration tests for ingestion -> pipeline -> API flow
- regression test set for model outputs
- schema compatibility checks for API and STAC records
- performance test on representative imagery volumes
- release checklist with rollback plan

## 90-Day Roadmap

### Days 1-30 (Foundation)

- scaffold repo and local environment
- stand up MinIO + PostGIS + API skeleton
- implement ingestion (upload + metadata extraction + checksum)
- implement STAC item creation and indexing
- add CI (lint, tests, build) and baseline observability

**Exit criteria:** can ingest datasets and query them spatially via API.

### Days 31-60 (Processing and ML)

- implement preprocessing pipeline (reprojection, tiling, normalization)
- integrate first inference model (baseline segmentation/detection)
- store outputs in object storage and metadata in PostGIS
- ship job orchestration with retries and failure handling
- add integration tests over end-to-end flow

**Exit criteria:** repeatable batch inference from raw imagery to consumable outputs.

### Days 61-90 (Production Hardening)

- build map/analysis UI for overlays and job status
- add auth/RBAC and audit logging
- add SLO dashboards and alert routing
- run load tests and tune pipeline throughput
- publish contributor docs, governance, and release policy

**Exit criteria:** v1 OSS release candidate with documented operations and on-call readiness.

## License and Governance

- **License recommendation:** Apache-2.0 (patent protection + broad adoption)
- **Governance model:** maintainers + CODEOWNERS + review requirements
- **Community docs:** CONTRIBUTING, SECURITY, SUPPORT, issue/PR templates

## Immediate Next Steps

1. Choose the initial use case (for example crop health segmentation or change detection).
2. Freeze v1 schema for dataset/job/output entities.
3. Implement ingestion + catalog first before advanced model work.
