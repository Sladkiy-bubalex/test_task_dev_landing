from loguru import logger

# Context manager for timing operations
import time
from contextlib import contextmanager


# Configure logging context for specific modules
def get_logger(name: str):
    """Get a logger with module context"""
    return logger.bind(module=name)


@contextmanager
def log_time(operation: str):
    """Log the time taken for an operation"""
    start = time.time()
    try:
        yield
    finally:
        duration = time.time() - start
        logger.info(f"Operation '{operation}' completed in {duration:.2f}s")
