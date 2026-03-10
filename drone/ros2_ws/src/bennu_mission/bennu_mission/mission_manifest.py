"""Mission manifest generator — produces contract v1 manifest.json and images.csv."""
import csv
import io
from collections import Counter
from typing import Optional


class ManifestGenerator:
    """Generates contract v1 compliant manifest.json and images.csv."""

    QUALITY_THRESHOLD = 0.5  # Score below this = failed

    def __init__(self, drone_id: str, hardware_manifest: dict, mission_id: str):
        """Initialize with drone identity and mission ID.

        Args:
            drone_id: Unique drone identifier (e.g., "bennu-001").
            hardware_manifest: Dict from DroneIdentity.hardware_manifest().
            mission_id: Unique mission identifier.
        """
        self._drone_id = drone_id
        self._hardware = hardware_manifest
        self._mission_id = mission_id

    def generate_manifest(
        self,
        images: list,
        sensor_config: str,
        trigger_mode: str = "distance",
        trigger_distance_m: float = 5.0,
        survey: Optional[dict] = None,
        checksums_digest: str = "",
        signature: str = "",
    ) -> dict:
        """Generate manifest.json dict.

        Args:
            images: List of ImageMetadata-like objects with .quality_score,
                    .quality_flags, .rtk_fix_type, .timestamp_utc attributes.
            sensor_config: Sensor configuration name (e.g., "survey", "mapping").
            trigger_mode: How images were triggered.
            trigger_distance_m: Distance between triggers.
            survey: Optional survey parameters dict.
            checksums_digest: SHA-256 of checksums.sha256 file.
            signature: Base64 Ed25519 signature.

        Returns:
            Dict matching contract/v1/manifest.schema.json.
        """
        quality_summary = self._compute_quality_summary(images)

        timestamps = [img.timestamp_utc for img in images]

        manifest = {
            "contract_version": "v1",
            "mission_id": self._mission_id,
            "drone_id": self._drone_id,
            "drone_hardware": self._hardware,
            "capture": {
                "start_time": min(timestamps) if timestamps else "",
                "end_time": max(timestamps) if timestamps else "",
                "image_count": len(images),
                "sensor_config": sensor_config,
                "trigger_mode": trigger_mode,
                "trigger_distance_m": trigger_distance_m,
            },
            "quality_summary": quality_summary,
            "checksums_digest": checksums_digest,
            "signature": signature,
        }

        if survey is not None:
            manifest["survey"] = survey

        return manifest

    def generate_images_csv(self, images: list) -> str:
        """Generate images.csv string with 18-column header.

        Args:
            images: List of objects with .to_csv_dict() method.

        Returns:
            CSV string with header and one row per image.
        """
        if not images:
            return ""

        output = io.StringIO()
        header = list(images[0].to_csv_dict().keys())
        writer = csv.DictWriter(output, fieldnames=header)
        writer.writeheader()
        for img in images:
            writer.writerow(img.to_csv_dict())
        return output.getvalue()

    def _compute_quality_summary(self, images: list) -> dict:
        """Compute quality summary from image list."""
        total = len(images)
        passed = sum(1 for img in images if img.quality_score >= self.QUALITY_THRESHOLD)
        failed = total - passed

        # Count failure reasons
        failure_reasons: Counter = Counter()
        for img in images:
            if img.quality_score < self.QUALITY_THRESHOLD:
                for flag in img.quality_flags.split(","):
                    flag = flag.strip()
                    if flag and flag != "ok":
                        failure_reasons[flag] += 1

        # RTK fixed percentage
        rtk_fixed = sum(1 for img in images if img.rtk_fix_type == "RTK_FIXED")
        rtk_fixed_pct = rtk_fixed / total if total > 0 else 0.0

        return {
            "images_total": total,
            "images_passed": passed,
            "images_failed": failed,
            "failure_reasons": dict(failure_reasons),
            "rtk_fixed_pct": round(rtk_fixed_pct, 4),
            "coverage_pct": None,  # Set by coverage tracker if survey grid defined
        }
