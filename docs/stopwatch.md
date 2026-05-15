# Stopwatch User Manual

The `cloudmesh.ai.common.stopwatch` module provides a thread-safe timing utility for measuring the execution time of code blocks. It is designed for benchmarking and performance profiling within cloudmesh-ai components.

## Overview

The `StopWatch` class allows you to start and stop multiple timers by name. Because it uses thread-local storage, timers in one thread do not interfere with timers in another, making it ideal for concurrent AI workloads.

## Key Features

- **Thread-Safe Timing**: Independent timers for each thread.
- **Cumulative Sums**: Automatically tracks the total time spent in a timer if it is started and stopped multiple times.
- **Benchmark Reporting**: A built-in `benchmark()` method that prints a formatted table of all timers, their status, and elapsed time.
- **Context Manager Support**: The `StopWatchBlock` class allows for easy timing using the `with` statement.

## Usage Guide

### Basic Timing

You can manually start and stop timers using a unique name.

```python
from cloudmesh.ai.common.stopwatch import StopWatch

# Start a timer
StopWatch.start("model_inference")

# ... perform the inference ...

# Stop the timer
StopWatch.stop("model_inference")

# Get the elapsed time
elapsed = StopWatch.get("model_inference")
print(f"Inference took {elapsed} seconds")
```

### Using the Context Manager

For a cleaner implementation, use `StopWatchBlock`.

```python
from cloudmesh.ai.common.stopwatch import StopWatchBlock

with StopWatchBlock("data_preprocessing"):
    # ... perform preprocessing ...
    pass
# Timer is automatically stopped and logged at the end of the block
```

### Generating a Benchmark Report

At the end of a process, you can print a summary of all recorded timers.

```python
from cloudmesh.ai.common.stopwatch import StopWatch

# ... after running various timed tasks ...

StopWatch.benchmark()
```

## API Reference

Refer to the auto-generated API documentation for detailed method signatures.