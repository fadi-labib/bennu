#!/usr/bin/env bash
# Set up Raspberry Pi 5 for Bennu drone companion computer
# Run on a fresh Ubuntu 22.04 Server install on the Pi 5
#
# Prerequisites:
#   - Ubuntu 22.04 Server flashed to microSD
#   - Pi 5 connected to internet via Ethernet or WiFi
#   - SSH access configured
#
# Usage: ssh pi@<ip> 'bash -s' < drone/setup_pi.sh

set -euo pipefail

echo "=== Bennu Pi 5 Setup ==="

# Update system
sudo apt update && sudo apt upgrade -y

# Install base dependencies
sudo apt install -y \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    htop \
    libcamera-apps \
    libcamera-dev \
    python3-libcamera \
    python3-picamera2 \
    exiftool

# Install ROS 2 Humble
echo "=== Installing ROS 2 Humble ==="
sudo apt install -y software-properties-common
sudo add-apt-repository universe -y
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
    | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
sudo apt update
sudo apt install -y ros-humble-ros-base ros-dev-tools

# Source ROS 2 in bashrc
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc

# Install Micro XRCE-DDS Agent
echo "=== Installing Micro XRCE-DDS Agent ==="
sudo snap install micro-xrce-dds-agent

# Enable UART for PX4 communication
echo "=== Configuring UART ==="
# Disable serial console on UART (needed for PX4 comms)
sudo systemctl disable serial-getty@ttyAMA0.service 2>/dev/null || true
# Add user to dialout group for UART access
sudo usermod -aG dialout $USER

# Create workspace directory
mkdir -p ~/bennu_ws/src

echo ""
echo "=== Setup Complete ==="
echo "Reboot required: sudo reboot"
echo "After reboot, verify:"
echo "  ros2 --version"
echo "  libcamera-hello --list-cameras"
echo "  micro-xrce-dds-agent --version"
