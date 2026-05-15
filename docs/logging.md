# Logging User Manual

The `cloudmesh.ai.common.logging` module provides a centralized logging framework designed for cloudmesh-ai components. It ensures consistent log formatting, simplifies log rotation, and supports advanced features like JSON logging and request tracing.

## Overview

Instead of using the standard `logging.getLogger()`, components should use the provided `get_logger()` function. This ensures that logs are routed to the correct directories and formatted according to project standards.

## Key Features

- **Centralized Configuration**: Automatically manages log directories and file naming based on the component name.
- **JSON Logging**: Support for structured logging, making it easier to ingest logs into ELK or other log analysis tools.
- **Request Tracing**: Uses thread-local storage to track requests across different function calls, allowing for a unique request ID to be attached to every log message.
- **Log Rotation**: Built-in support for rotating log files to prevent disk space exhaustion.

## Usage Guide

### Basic Logging

To get a logger for your component, call `get_logger` with the component name.

```python
from cloudmesh.ai.common.logging import get_logger

logger = get_logger("my_ai_component")

logger.info("This is an informational message")
logger.warning("This is a warning message")
logger.error("This is an error message")
```

### Request Tracing

Request tracing allows you to correlate logs for a single operation across multiple threads or function calls.

```python
from cloudmesh.ai.common.logging import set_request_id

# Set a unique ID for the current thread/request
set_request_id("req-12345")

logger = get_logger("my_ai_component")
logger.info("Processing request") # Log will include [req-12345]
```

## API Reference

Refer to the auto-generated API documentation for detailed function signatures and configuration options.