#!/usr/bin/env python3
"""
Inspect ODM output: load point cloud, print stats, optionally visualize.

Usage:
    python3 ground/analysis/inspect_model.py <odm_output_dir>
    python3 ground/analysis/inspect_model.py <odm_output_dir> --visualize
"""

import argparse
import os
import sys


def find_output_files(odm_dir: str) -> dict:
    """Find ODM output files in the given directory."""
    files = {}

    # Point cloud
    for ext in [".laz", ".las", ".ply"]:
        for root, _, filenames in os.walk(odm_dir):
            for f in filenames:
                if f.endswith(ext):
                    files.setdefault("pointcloud", []).append(os.path.join(root, f))

    # Mesh
    for root, _, filenames in os.walk(odm_dir):
        for f in filenames:
            if f.endswith(".obj"):
                files.setdefault("mesh", []).append(os.path.join(root, f))

    # Orthophoto
    for root, _, filenames in os.walk(odm_dir):
        for f in filenames:
            if f.endswith(".tif") and "orthophoto" in root:
                files.setdefault("orthophoto", []).append(os.path.join(root, f))

    # DSM/DTM
    for root, _, filenames in os.walk(odm_dir):
        for f in filenames:
            if f.endswith(".tif") and "dem" in root:
                files.setdefault("dem", []).append(os.path.join(root, f))

    return files


def inspect_pointcloud(filepath: str, visualize: bool = False):
    """Load and inspect a point cloud file."""
    try:
        import open3d as o3d
    except ImportError:
        print("  open3d not installed. Install: pip install open3d")
        return

    print(f"\n  Loading: {filepath}")
    pcd = o3d.io.read_point_cloud(filepath)

    points = len(pcd.points)
    bbox = pcd.get_axis_aligned_bounding_box()
    extent = bbox.get_extent()

    print(f"  Points: {points:,}")
    print(f"  Bounding box: {extent[0]:.1f} x {extent[1]:.1f} x {extent[2]:.1f} m")
    print(f"  Has colors: {pcd.has_colors()}")
    print(f"  Has normals: {pcd.has_normals()}")

    if visualize:
        print("  Opening 3D viewer...")
        o3d.visualization.draw_geometries([pcd])


def main():
    parser = argparse.ArgumentParser(description="Inspect ODM output")
    parser.add_argument("odm_dir", help="Path to ODM output directory")
    parser.add_argument("--visualize", action="store_true", help="Open 3D viewer")
    args = parser.parse_args()

    if not os.path.isdir(args.odm_dir):
        print(f"Error: {args.odm_dir} not found")
        sys.exit(1)

    print(f"=== Inspecting ODM Output: {args.odm_dir} ===")

    files = find_output_files(args.odm_dir)

    if not files:
        print("No ODM output files found.")
        sys.exit(1)

    for category, paths in files.items():
        print(f"\n{category.upper()}:")
        for p in paths:
            size_mb = os.path.getsize(p) / (1024 * 1024)
            print(f"  {os.path.basename(p)} ({size_mb:.1f} MB)")

            if category == "pointcloud" and p.endswith(".ply"):
                inspect_pointcloud(p, args.visualize)


if __name__ == "__main__":
    main()
