# Mission Bundle Contract v1

The mission bundle is the **only** integration point between the Bennu drone
(data acquisition) and any downstream analysis platform. Both sides can change
internals freely as long as the contract is honoured.

## Bundle Structure

```
{mission_id}/
├── manifest.json           # Mission-level metadata (signed)
├── images/                 # Captured images
├── metadata/
│   ├── images.csv          # Per-image metadata (18 columns)
│   └── calibration.csv     # Ambient light / panel readings (if applicable)
├── telemetry/
│   └── flight.ulg          # PX4 flight log
├── quality/
│   └── report.json         # Per-image quality scores + summary
└── checksums.sha256        # SHA-256 hashes of all files
```

## Schema Files

| File | Purpose |
|------|---------|
| `manifest.schema.json` | JSON Schema (draft-07) for `manifest.json` |
| `images.schema.json` | Column definitions for `metadata/images.csv` |

## Validation

Install `jsonschema` (Python) and validate the manifest:

```python
import json
from jsonschema import validate

with open("contract/v1/manifest.schema.json") as f:
    schema = json.load(f)
with open("path/to/manifest.json") as f:
    manifest = json.load(f)

validate(instance=manifest, schema=schema)
```

For CSV validation, load `images.schema.json` and verify that the CSV header
row matches the `columns[*].name` values in order.

## Versioning Rules

- **Patch** (v1.0.1): Documentation or description changes only. No structural changes.
- **Minor** (v1.1): Add optional fields only. Existing consumers are unaffected.
- **Major** (v2): May remove or rename fields. Migration notes required.

A minor version bump never removes or renames a field. Consumers that understand
v1 can safely ignore unknown optional fields added in v1.x.

## Integrity Chain

1. Compute SHA-256 of every file in the bundle **except** `manifest.json` and
   `checksums.sha256` itself, then write the result to `checksums.sha256`.
   (`manifest.json` is excluded because it embeds `checksums_digest` — a hash of
   `checksums.sha256` — creating a circular dependency if included.)
2. Compute SHA-256 of `checksums.sha256` and set `checksums_digest` in the manifest.
3. Serialize the manifest to canonical JSON (`json.dumps(m, sort_keys=True, separators=(',', ':'))`), excluding the `signature` field.
4. Sign the canonical bytes with the drone's Ed25519 private key.
5. Set `signature` in the manifest (base64-encoded).

The platform verifies this chain on ingest: the Ed25519 signature protects
`manifest.json`, `checksums_digest` inside the manifest protects `checksums.sha256`,
and `checksums.sha256` protects every other file in the bundle.
