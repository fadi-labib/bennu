"""Mission bundle packager — assembles the complete bundle directory."""

import hashlib
import json
import re
import shutil
from pathlib import Path


class BundlePackager:
    """Assembles a mission bundle directory with all required files."""

    # Safe mission ID pattern: alphanumeric, hyphens, underscores, dots
    _SAFE_ID_RE = re.compile(r"^[\w.\-]+$")

    def __init__(self, output_dir: Path):
        self._output_dir = Path(output_dir)

    def package(
        self,
        mission_id: str,
        manifest: dict,
        images_csv: str,
        image_files: list[Path],
        flight_log: Path | None = None,
        quality_report: dict | None = None,
    ) -> Path:
        """Assemble the complete bundle directory.

        Returns path to the created bundle directory.

        Raises:
            ValueError: If mission_id contains unsafe path characters.
            FileNotFoundError: If flight_log is specified but does not exist.
            OSError: If any filesystem operation fails (partial bundle is cleaned up).
        """
        if not self._SAFE_ID_RE.match(mission_id):
            raise ValueError(
                f"Unsafe mission_id: {mission_id!r} — "
                "use only alphanumeric, hyphens, underscores, dots"
            )

        if flight_log is not None and not flight_log.exists():
            raise FileNotFoundError(f"Flight log not found: {flight_log}")

        bundle_dir = self._output_dir / mission_id
        try:
            # Remove existing bundle to prevent stale files from prior runs
            if bundle_dir.exists():
                shutil.rmtree(bundle_dir)
            bundle_dir.mkdir(parents=True)

            # contract_version marker
            (bundle_dir / "contract_version").write_text("v1\n")

            # images/
            images_dir = bundle_dir / "images"
            images_dir.mkdir(exist_ok=True)
            seen_names: set = set()
            for img in image_files:
                if img.name in seen_names:
                    raise ValueError(f"Duplicate image filename: {img.name}")
                seen_names.add(img.name)
                shutil.copy2(img, images_dir / img.name)

            # metadata/
            metadata_dir = bundle_dir / "metadata"
            metadata_dir.mkdir(exist_ok=True)
            (metadata_dir / "images.csv").write_text(images_csv)

            # telemetry/
            telemetry_dir = bundle_dir / "telemetry"
            telemetry_dir.mkdir(exist_ok=True)
            if flight_log is not None:
                shutil.copy2(flight_log, telemetry_dir / "flight.ulg")

            # quality/
            quality_dir = bundle_dir / "quality"
            quality_dir.mkdir(exist_ok=True)
            if quality_report is None:
                report = {"status": "not_available"}
            else:
                report = quality_report
            (quality_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n")

            # checksums.sha256 — hash every file in the bundle
            checksums = self._compute_checksums(bundle_dir)
            checksums_path = bundle_dir / "checksums.sha256"
            checksums_path.write_text(checksums)

            # Write manifest.json (caller should set checksums_digest before signing)
            (bundle_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

            return bundle_dir
        except Exception:
            # Clean up partial bundle to avoid corrupted state
            if bundle_dir.exists():
                shutil.rmtree(bundle_dir, ignore_errors=True)
            raise

    @staticmethod
    def compute_checksums_digest(bundle_dir: Path) -> str:
        """Compute SHA-256 of the checksums.sha256 file itself."""
        checksums_path = bundle_dir / "checksums.sha256"
        return hashlib.sha256(checksums_path.read_bytes()).hexdigest()

    @staticmethod
    def _compute_checksums(bundle_dir: Path) -> str:
        """Compute SHA-256 for every file in the bundle.

        Excludes checksums.sha256 (self-reference) and manifest.json
        (contains checksums_digest, creating a circular dependency).
        manifest.json is instead protected by the Ed25519 signature.
        """
        excluded = {Path("checksums.sha256"), Path("manifest.json")}
        lines = []
        for path in sorted(bundle_dir.rglob("*")):
            if path.is_file():
                rel = path.relative_to(bundle_dir)
                if rel not in excluded:
                    sha = hashlib.sha256(path.read_bytes()).hexdigest()
                    lines.append(f"{sha}  {rel}")
        return "\n".join(lines) + "\n"
