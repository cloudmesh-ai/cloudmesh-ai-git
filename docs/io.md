# I/O Utilities User Manual

The `cloudmesh.ai.common.io` module provides a set of helper functions for common input/output operations, focusing on cross-platform path handling, YAML configuration management, and benchmark data generation.

## Overview

This module simplifies the process of interacting with the file system and configuration files, ensuring that paths are resolved correctly regardless of the operating system (Windows, macOS, or Linux).

## Key Features

- **Smart Path Expansion**: Resolves `~`, environment variables, and relative path components (`.` and `..`) into absolute paths.
- **Safe YAML Handling**: Provides wrappers for loading and dumping YAML files with built-in error handling and directory creation.
- **Benchmark File Generation**: Utilities to create dummy files of specific sizes or YAML files with a large number of service entries for performance testing.

## Usage Guide

### Path Expansion

Use `path_expand` to ensure a path is absolute and compatible with the current OS.

```python
from cloudmesh.ai.common.io import path_expand

# Expands ~ and environment variables
path = path_expand("~/my_project/$VERSION/config.yaml")
print(path) # Output: /home/user/my_project/1.0/config.yaml (on Linux)
```

### Working with YAML

The `load_yaml` and `dump_yaml` functions provide a safe way to handle configuration files.

```python
from pathlib import Path
from cloudmesh.ai.common.io import load_yaml, dump_yaml

config_path = Path("config.yaml")

# Load YAML safely
data = load_yaml(config_path)

# Modify data
if data:
    data['version'] = '2.0'

# Save YAML (automatically creates parent directories)
dump_yaml(config_path, data)
```

### Creating Benchmark Files

For performance testing, you can generate large files or complex YAML structures.

```python
from cloudmesh.ai.common.io import create_benchmark_file, create_benchmark_yaml

# Create a 100MB binary file for I/O testing
create_benchmark_file("/tmp/test_file.bin", 100)

# Create a YAML file with 1000 service entries
create_benchmark_yaml("/tmp/benchmark.yaml", 1000)
```

## API Reference

Refer to the auto-generated API documentation for detailed function signatures.