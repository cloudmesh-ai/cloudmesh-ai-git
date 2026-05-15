# Telemetry User Manual

The `cloudmesh.ai.common.telemetry` module provides a standardized way to record and emit performance metrics, system state, and event data during the execution of AI workloads. This data is essential for benchmarking, debugging, and monitoring the efficiency of AI models.

## Overview

The `Telemetry` class acts as the primary interface for recording data. It supports emitting metrics to various backends (such as JSONL files or SQLite databases), allowing for both real-time monitoring and post-hoc analysis.

## Key Features

- **Flexible Metric Emission**: Record scalar values, dictionaries of metrics, and status updates.
- **Automatic Context Capture**: Automatically captures system information (CPU, GPU, RAM) and user context when emitting telemetry.
- **Pluggable Backends**: Support for multiple storage formats to balance between performance (JSONL) and queryability (SQLite).
- **Async Support**: Designed to work within asynchronous workflows common in AI service implementations.

## Usage Guide

### Basic Telemetry Emission

To record a metric, instantiate the `Telemetry` class and use the `emit` method.

```python
from cloudmesh.ai.common.telemetry import Telemetry

t = Telemetry()

# Emit a simple metric
t.emit(metric="inference_latency", value=0.125, status="completed")

# Emit multiple metrics at once
t.emit(metrics={"tokens_per_sec": 45.2, "gpu_util": 88}, status="completed")
```

### Recording Events

Events are used to mark specific milestones in a process (e.g., "model_loaded", "request_received").

```python
from cloudmesh.ai.common.telemetry import Telemetry

t = Telemetry()
t.emit(event="model_load_start", status="started")
# ... load model ...
t.emit(event="model_load_end", status="completed")
```

### Configuring the Backend

You can specify where the telemetry data should be stored.

```python
from cloudmesh.ai.common.telemetry import Telemetry

# Store telemetry in a SQLite database for easier querying
t = Telemetry(backend="sqlite", path="telemetry.db")
t.emit(metric="accuracy", value=0.92)
```

## API Reference

Refer to the auto-generated API documentation for detailed method signatures and backend configuration options.