"""
Structured logging configuration for Greptile MCP Server.

This module provides comprehensive logging with structured output,
performance monitoring, and error tracking.
"""

import os
import sys
import json
import time
import logging
import traceback
from typing import Any, Dict, Optional, Union
from datetime import datetime
from functools import wraps
from contextlib import contextmanager


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add request context if available
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        
        if hasattr(record, 'session_id'):
            log_entry["session_id"] = record.session_id
        
        if hasattr(record, 'tool_name'):
            log_entry["tool_name"] = record.tool_name
        
        return json.dumps(log_entry)


class GreptileLogger:
    """Enhanced logger for Greptile MCP Server with structured logging."""
    
    def __init__(self, name: str = "greptile-mcp"):
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Configure the logger with appropriate handlers and formatters."""
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set log level from environment
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.logger.setLevel(getattr(logging, log_level, logging.INFO))
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        
        # Use structured logging in production, simple format in development
        if os.getenv("ENVIRONMENT", "development") == "production":
            console_handler.setFormatter(StructuredFormatter())
        else:
            console_handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            )
        
        self.logger.addHandler(console_handler)
        
        # Prevent duplicate logs
        self.logger.propagate = False
    
    def _log_with_context(self, level: int, message: str, **kwargs):
        """Log with additional context information."""
        extra = {"extra_fields": kwargs} if kwargs else {}
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with context."""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message with context."""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context."""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with context."""
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with context."""
        self._log_with_context(logging.CRITICAL, message, **kwargs)
    
    def log_api_call(self, method: str, url: str, status_code: int = None, 
                     duration: float = None, **kwargs):
        """Log API call with structured information."""
        self.info(
            f"API call: {method} {url}",
            method=method,
            url=url,
            status_code=status_code,
            duration_ms=duration * 1000 if duration else None,
            **kwargs
        )
    
    def log_tool_execution(self, tool_name: str, duration: float = None, 
                          success: bool = True, **kwargs):
        """Log MCP tool execution."""
        level = logging.INFO if success else logging.ERROR
        message = f"Tool execution {'completed' if success else 'failed'}: {tool_name}"
        
        self._log_with_context(
            level,
            message,
            tool_name=tool_name,
            duration_ms=duration * 1000 if duration else None,
            success=success,
            **kwargs
        )
    
    def log_validation_error(self, field: str, error: str, value: Any = None, **kwargs):
        """Log validation error with context."""
        self.error(
            f"Validation error in field '{field}': {error}",
            field=field,
            validation_error=error,
            invalid_value=str(value) if value is not None else None,
            **kwargs
        )
    
    def log_exception(self, exception: Exception, context: str = None, **kwargs):
        """Log exception with full context and traceback."""
        message = f"Exception in {context}: {str(exception)}" if context else str(exception)
        
        # Use the logger's exception method to capture traceback
        self.logger.exception(
            message,
            extra={"extra_fields": kwargs} if kwargs else {}
        )


# Global logger instance
logger = GreptileLogger()


def log_execution_time(tool_name: str = None):
    """Decorator to log function execution time."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            func_name = tool_name or func.__name__
            
            try:
                logger.debug(f"Starting execution: {func_name}")
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.log_tool_execution(
                    func_name,
                    duration=duration,
                    success=True
                )
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.log_tool_execution(
                    func_name,
                    duration=duration,
                    success=False,
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            func_name = tool_name or func.__name__
            
            try:
                logger.debug(f"Starting execution: {func_name}")
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.log_tool_execution(
                    func_name,
                    duration=duration,
                    success=True
                )
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.log_tool_execution(
                    func_name,
                    duration=duration,
                    success=False,
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


@contextmanager
def log_context(**context_vars):
    """Context manager to add context variables to all logs within the block."""
    # This is a simplified implementation
    # In a full implementation, you'd use contextvars or similar
    try:
        yield
    finally:
        pass


class APICallLogger:
    """Context manager for logging API calls with timing and error handling."""
    
    def __init__(self, method: str, url: str, **context):
        self.method = method
        self.url = url
        self.context = context
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        logger.debug(
            f"Starting API call: {self.method} {self.url}",
            **self.context
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type is None:
            # Success
            logger.log_api_call(
                self.method,
                self.url,
                duration=duration,
                **self.context
            )
        else:
            # Error
            logger.error(
                f"API call failed: {self.method} {self.url}",
                duration_ms=duration * 1000,
                error=str(exc_val),
                error_type=exc_type.__name__,
                **self.context
            )


def setup_logging():
    """Initialize logging configuration for the application."""
    # This function can be called at application startup
    # to ensure logging is properly configured
    global logger
    logger = GreptileLogger()
    
    logger.info(
        "Logging system initialized",
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        environment=os.getenv("ENVIRONMENT", "development")
    )


# Performance monitoring utilities
class PerformanceMonitor:
    """Monitor and log performance metrics."""
    
    @staticmethod
    def log_memory_usage():
        """Log current memory usage."""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            logger.info(
                "Memory usage",
                memory_rss_mb=memory_info.rss / 1024 / 1024,
                memory_vms_mb=memory_info.vms / 1024 / 1024,
                memory_percent=process.memory_percent()
            )
        except ImportError:
            logger.warning("psutil not available for memory monitoring")
    
    @staticmethod
    def log_system_info():
        """Log system information at startup."""
        logger.info(
            "System information",
            python_version=sys.version,
            platform=sys.platform,
            environment=os.getenv("ENVIRONMENT", "development")
        )
