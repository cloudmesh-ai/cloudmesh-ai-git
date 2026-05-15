# Telemetry Aggregation User Manual

The `cloudmesh.ai.common.aggregation` module provides tools to analyze and summarize telemetry data collected during AI workloads. It allows users to transform raw telemetry records (from JSONL or SQLite) into actionable insights.

## Overview

The primary class is `TelemetryAggregator`, which handles data loading and provides methods for statistical analysis.

## Key Features

- **Multi-source Loading**: Automatically detects and loads data from `.db` (SQLite) or `.jsonl` files.
- **High-level Summaries**: Quickly calculate success rates and distribution of commands.
- **Metric Aggregation**: Compute average, minimum, and maximum values for specific performance metrics.

## Usage Guide

### Initializing the Aggregator

To start analyzing data, instantiate the `TelemetryAggregator` with the path to your telemetry file.

```python
from cloudmesh.ai.common.aggregation import TelemetryAggregator

# Load from a SQLite database
agg = TelemetryAggregator("telemetry.db")

# Or load from a JSONL file
# agg = TelemetryAggregator("telemetry.jsonl")
```

### Generating a Summary

The `get_summary()` method provides a snapshot of the overall execution health.

```python
summary = agg.get_summary()
print(f"Total Records: {summary['total_records']}")
print(f"Success Rate: {summary['success_rate']}")
print(f"Status Distribution: {summary['status_distribution']}")
```

### Aggregating Specific Metrics

If you have recorded specific metrics (e.g., `inference_time`, `token_count`), you can aggregate them across all records.

```python
# Calculate stats for 'inference_time'
stats = agg.aggregate_metric("inference_time")
print(f"Average Time: {stats['avg']}")
print(f"Max Time: {stats['max']}")
```

## API Reference

Refer to the auto-generated API documentation for detailed method signatures.