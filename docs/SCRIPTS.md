# Scripts Documentation

This document provides information about the utility scripts included in the `scripts/` directory.

## Installation Scripts

### Linux Installation

- `install_ubuntu.sh`: Installation script for Ubuntu-based systems
- `install_fedora.sh`: Installation script for Fedora-based systems

### macOS Installation

- `install_macos.sh`: Installation script for macOS systems

### Windows Installation

- `install_windows.ps1`: PowerShell installation script for Windows systems

## Hardware Configuration

- `configure_hardware.sh`: Configuration script for Linux/macOS systems
- `configure_hardware.ps1`: PowerShell configuration script for Windows systems
- `optimize_rpi.sh`: Optimization script specifically for Raspberry Pi devices

## Model Management

- `install_models.sh`: Script to download and install required ML models

## Service Management

- `setup_service.sh`: Script to set up rtaspi as a system service

## Usage

### Linux/macOS

```bash
# Installation
./scripts/install_ubuntu.sh    # For Ubuntu
./scripts/install_fedora.sh    # For Fedora
./scripts/install_macos.sh     # For macOS

# Hardware configuration
./scripts/configure_hardware.sh

# Raspberry Pi optimization
./scripts/optimize_rpi.sh

# Install ML models
./scripts/install_models.sh

# Service setup
./scripts/setup_service.sh
```

### Windows

```powershell
# Installation
.\scripts\install_windows.ps1

# Hardware configuration
.\scripts\configure_hardware.ps1
```

## Script Details

### Installation Scripts

These scripts handle the installation of rtaspi and its dependencies:

- Install required system packages
- Set up Python environment
- Install Python dependencies
- Configure system paths
- Set up necessary permissions

### Hardware Configuration Scripts

The hardware configuration scripts:

- Detect available hardware devices
- Configure device permissions
- Set up necessary kernel modules
- Configure audio/video devices
- Set up USB device permissions

### Raspberry Pi Optimization

The `optimize_rpi.sh` script performs Raspberry Pi specific optimizations:

- Configures GPU memory split
- Optimizes system settings for video processing
- Sets up hardware acceleration
- Tunes performance parameters

### Model Installation

The `install_models.sh` script:

- Downloads required ML models
- Sets up model paths
- Validates model installations
- Configures model-specific settings

### Service Setup

The `setup_service.sh` script:

- Creates necessary service files
- Configures service parameters
- Sets up auto-start
- Configures logging
- Sets up proper permissions
