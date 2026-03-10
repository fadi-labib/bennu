"""Mission bundle packager — assembles the complete bundle directory."""
import hashlib
import json
import shutil
from pathlib import Path
from typing import List, Optional


class BundlePackager:
    """Assembles a mission bundle directory with all required files."""

    def __init__(self, output_dir: Path):
        self._output_dir = Path(output_dir)

    def package(
        self,
        mission_id: str,
        manifest: dict,
        images_csv: str,
        image_files: List[Path],
        flight_log: Optional[Path] = None,
        quality_report: Optional[dict] = None,
    ) -> Path:
        """Assemble the complete bundle directory.

        Returns path to the created bundle directory.
        """
        bundle_dir = self._output_dir / mission_id
        bundle_dir.mkdir(parents=True, exist_ok=True)

        # contract_version marker
        (bundle_dir / "contract_version").write_text("v1\n")

        # images/
        images_dir = bundle_dir / "images"
        images_dir.mkdir(exist_ok=True)
        for img in image_files:
            shutil.copy2(img, images_dir / img.name)

        # metadata/
        metadata_dir = bundle_dir / "metadata"
        metadata_dir.mkdir(exist_ok=True)
        (metadata_dir / "images.csv").write_text(images_csv)

        # telemetry/
        telemetry_dir = bundle_dir / "telemetry"
        telemetry_dir.mkdir(exist_ok=True)
        if flight_log and flight_log.exists():
            shutil.copy2(flight_log, telemetry_dir / "flight.ulg")

        # quality/
        quality_dir = bundle_dir / "quality"
        quality_dir.mkdir(exist_ok=True)
        report = quality_report or {}
        (quality_dir / "report.json").write_text(
            json.dumps(report, indent=2) + "\n"
        )

        # checksums.sha256 — hash every file in the bundle
        checksums = self._compute_checksums(bundle_dir)
        checksums_path = bundle_dir / "checksums.sha256"
        checksums_path.write_text(checksums)

        # Write manifest.json (caller should set checksums_digest before signing)
        (bundle_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n"
        )

        return bundle_dir

    @staticmethod
    def compute_checksums_digest(bundle_dir: Path) -> str:
        """Compute SHA-256 of the checksums.sha256 file itself."""
        checksums_path = bundle_dir / "checksums.sha256"
        return hashlib.sha256(checksums_path.read_bytes()).hexdigest()

    @staticmethod
    def _compute_checksums(bundle_dir: Path) -> str:
        """Compute SHA-256 for every file in the bundle (excluding checksums.sha256 itself)."""
        lines = []
        for path in sorted(bundle_dir.rglob("*")):
            if path.is_file() and path.name != "checksums.sha256" and path.name != "manifest.json":
                rel = path.relative_to(bundle_dir)
                sha = hashlib.sha256(path.read_bytes()).hexdigest()
                lines.append(f"{sha}  {rel}")
        return "\n".join(lines) + "\n"
