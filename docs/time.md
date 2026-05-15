# Time Utilities User Manual

The `cloudmesh.ai.common.time` module provides high-resolution timing and standardized time formatting utilities. It ensures that timestamps and durations are handled consistently across all cloudmesh-ai components, which is critical for accurate telemetry and logging.

## Overview

This module abstracts the complexities of time zone handling and high-precision clock access, providing a set of helpers to generate human-readable timestamps and calculate precise intervals.

## Key Features

- **High-Resolution Timing**: Access to monotonic clocks for measuring durations without being affected by system clock updates.
- **Standardized Formatting**: Consistent ISO-8601 and custom timestamp formats for logs and telemetry.
- **Timezone Awareness**: Helpers to ensure timestamps are recorded in a consistent timezone (typically UTC) to allow for correlation across distributed systems.

## Usage Guide

### Generating Timestamps

Use the provided formatting functions to create consistent timestamps for your logs.

```python
from cloudmesh.ai.common.time import now, format_time

# Get current time in a standardized format
timestamp = now()
print(f"Current time: {timestamp}")

# Format a specific time object
formatted = format_time(timestamp, "%Y-%m-%d %H:%M:%S")
print(f"Formatted: {formatted}")
```

### Measuring Intervals

For precise measurement of code execution, use the timing helpers.

```python
from cloudmesh.ai.common.time import timer

with timer("inference_step"):
    # ... perform AI inference ...
    pass

# The duration is recorded and can be retrieved for telemetry
```

## API Reference

Refer to the auto-generated API documentation for detailed function signatures.