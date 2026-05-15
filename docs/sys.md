# System Utilities User Manual

The `cloudmesh.ai.common.sys` module provides a comprehensive set of tools for interacting with the underlying operating system and hardware. It is designed to provide consistent system information across different platforms (Windows, macOS, Linux, and Raspberry Pi).

## Overview

This module is used to detect the environment, retrieve hardware specifications (CPU, GPU, RAM), and monitor real-time system metrics. It abstracts the differences between operating systems, allowing cloudmesh-ai components to adapt their behavior based on the available resources.

## Key Features

- **OS Detection**: Reliable functions to identify if the system is running Windows, macOS, Linux, or Raspberry Pi OS.
- **Hardware Discovery**: Tools to retrieve detailed information about the CPU, memory, and available GPUs (including NVIDIA and Apple Silicon).
- **System Metrics**: Real-time collection of CPU load, memory usage, and disk space.
- **Environment Helpers**: Detection of GUI environments (window managers) and system locale.

## Usage Guide

### OS Detection

Use the `os_is_*` functions to implement platform-specific logic.

```python
from cloudmesh.ai.common.sys import os_is_linux, os_is_windows, os_is_mac

if os_is_linux():
    print("Running on Linux")
elif os_is_windows():
    print("Running on Windows")
elif os_is_mac():
    print("Running on macOS")
```

### Retrieving System Information

The `systeminfo()` function provides a comprehensive dictionary of the current system's hardware and software state.

```python
from cloudmesh.ai.common.sys import systeminfo

info = systeminfo()
print(f"OS: {info.get('os')}")
print(f"CPU: {info.get('cpu')}")
print(f"Total Memory: {info.get('memory_total')}")
```

### Checking for GUI Support

If your component needs to launch a window or a plot, check if a window manager is available.

```python
from cloudmesh.ai.common.sys import has_window_manager

if has_window_manager():
    print("GUI environment detected. Launching window...")
else:
    print("Headless environment. Running in CLI mode.")
```

## API Reference

Refer to the auto-generated API documentation for detailed function signatures.