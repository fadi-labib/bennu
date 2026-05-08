#!/usr/bin/env bash
# Set up NVIDIA Container Toolkit for Docker GPU access (Gazebo rendering)
# Usage: sudo bash sim/setup_nvidia_docker.sh
set -euo pipefail

echo "=== Installing NVIDIA Container Toolkit ==="

curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
    | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
    | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
    | tee /etc/apt/sources.list.d/nvidia-container-toolkit.list > /dev/null

apt-get update -qq
apt-get install -y nvidia-container-toolkit

echo "=== Configuring Docker runtime ==="
nvidia-ctk runtime configure --runtime=docker
systemctl restart docker

echo ""
echo "=== Done ==="
echo "Now run:"
echo "  xhost +local:docker"
echo "  make dev-debug"
