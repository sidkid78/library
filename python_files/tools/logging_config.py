"""
Logging Configuration for Agent Tools

Provides comprehensive file-based logging for orchestrator, agent_fork, 
and context_summarizer modules.

Usage:
    from .logging_config import get_logger, setup_logging
    
    # Get a logger for your module
    logger = get_logger(__name__)
    
    # Log at various levels
    logger.debug("Debug info")
    logger.info("Info message")
    logger.warning("Warning!")
    logger.error("Error occurred", exc_info=True)
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import json

# Default log directory
DEFAULT_LOG_DIR = Path(__file__).parent.parent / "logs"


class JSONFormatter(logging.Formatter):
    """Format log records as JSON for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            log_data["data"] = record.extra_data
            
        return json.dumps(log_data)


class DetailedFormatter(logging.Formatter):
    """Detailed human-readable format for console/file logging."""
    
    FORMATS = {
        logging.DEBUG: "\033[36m%(asctime)s [DEBUG] %(name)s:%(funcName)s:%(lineno)d - %(message)s\033[0m",
        logging.INFO: "\033[32m%(asctime)s [INFO] %(name)s - %(message)s\033[0m",
        logging.WARNING: "\033[33m%(asctime)s [WARNING] %(name)s:%(funcName)s - %(message)s\033[0m",
        logging.ERROR: "\033[31m%(asctime)s [ERROR] %(name)s:%(funcName)s:%(lineno)d - %(message)s\033[0m",
        logging.CRITICAL: "\033[41m%(asctime)s [CRITICAL] %(name)s:%(funcName)s:%(lineno)d - %(message)s\033[0m",
    }
    
    def format(self, record: logging.LogRecord) -> str:
        log_fmt = self.FORMATS.get(record.levelno, self.FORMATS[logging.INFO])
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)


class PlainFormatter(logging.Formatter):
    """Plain format for file logging (no ANSI colors)."""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


def setup_logging(
    log_dir: Optional[Path] = None,
    level: int = logging.DEBUG,
    console_level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    enable_json: bool = True,
    enable_console: bool = True
) -> Path:
    """
    Set up comprehensive logging for all agent tools.
    
    Args:
        log_dir: Directory for log files. Defaults to ./logs
        level: File logging level
        console_level: Console logging level
        max_bytes: Max size per log file before rotation
        backup_count: Number of backup files to keep
        enable_json: Also create JSON-formatted logs
        enable_console: Enable console output
        
    Returns:
        Path to the log directory
    """
    log_dir = log_dir or DEFAULT_LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a date-stamped session log directory
    session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    session_dir = log_dir / session_id
    session_dir.mkdir(exist_ok=True)
    
    # Get the root logger for our tools
    root_logger = logging.getLogger('agent_tools')
    root_logger.setLevel(logging.DEBUG)  # Capture all, filter at handler level
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # === Main Log File (rotating) ===
    main_log_path = session_dir / "agent_tools.log"
    file_handler = logging.handlers.RotatingFileHandler(
        main_log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(PlainFormatter())
    root_logger.addHandler(file_handler)
    
    # === JSON Log File (for structured analysis) ===
    if enable_json:
        json_log_path = session_dir / "agent_tools.json"
        json_handler = logging.handlers.RotatingFileHandler(
            json_log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        json_handler.setLevel(level)
        json_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(json_handler)
    
    # === Module-specific log files ===
    modules = ['orchestrator', 'agent_fork', 'context_summarizer', 'agent_tools']
    for module in modules:
        module_log_path = session_dir / f"{module}.log"
        module_handler = logging.handlers.RotatingFileHandler(
            module_log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        module_handler.setLevel(logging.DEBUG)
        module_handler.setFormatter(PlainFormatter())
        
        # Add filter to only capture logs from this module
        module_handler.addFilter(lambda record, m=module: m in record.name)
        root_logger.addHandler(module_handler)
    
    # === Console Handler ===
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_level)
        console_handler.setFormatter(DetailedFormatter())
        root_logger.addHandler(console_handler)
    
    # === Error-only log file ===
    error_log_path = session_dir / "errors.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(PlainFormatter())
    root_logger.addHandler(error_handler)
    
    # Create a symlink to latest session
    latest_link = log_dir / "latest"
    if latest_link.exists() or latest_link.is_symlink():
        latest_link.unlink()
    try:
        latest_link.symlink_to(session_dir.name)
    except OSError:
        # Symlinks might not work on Windows without admin
        pass
    
    # Log setup completion
    root_logger.info(f"Logging initialized. Session: {session_id}")
    root_logger.info(f"Log directory: {session_dir}")
    
    return session_dir


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    Args:
        name: Module name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    # Ensure name is under our namespace
    if not name.startswith('agent_tools'):
        name = f"agent_tools.{name}"
    
    return logging.getLogger(name)


class LogContext:
    """Context manager for adding extra data to log records."""
    
    def __init__(self, logger: logging.Logger, **kwargs):
        self.logger = logger
        self.extra_data = kwargs
        self._old_factory = None
    
    def __enter__(self):
        self._old_factory = logging.getLogRecordFactory()
        extra = self.extra_data
        
        def factory(*args, **kwargs):
            record = self._old_factory(*args, **kwargs)
            record.extra_data = extra
            return record
        
        logging.setLogRecordFactory(factory)
        return self
    
    def __exit__(self, *args):
        logging.setLogRecordFactory(self._old_factory)


# Convenience functions for common logging patterns
def log_api_call(logger: logging.Logger, model: str, task: str, **kwargs):
    """Log an API call with relevant details."""
    logger.info(f"API Call: model={model}, task_preview={task[:100]}...")
    logger.debug(f"API Call details: {kwargs}")


def log_api_response(logger: logging.Logger, model: str, status: str, tokens: Optional[int] = None, **kwargs):
    """Log an API response with usage info."""
    logger.info(f"API Response: model={model}, status={status}, tokens={tokens}")
    logger.debug(f"API Response details: {kwargs}")


def log_workflow_step(logger: logging.Logger, workflow_id: str, step_id: str, action: str, **kwargs):
    """Log a workflow step execution."""
    logger.info(f"Workflow {workflow_id}: Step {step_id} - {action}")
    if kwargs:
        logger.debug(f"Step details: {kwargs}")


def log_tool_execution(logger: logging.Logger, tool_name: str, arguments: dict, result: dict):
    """Log a tool execution."""
    logger.info(f"Tool: {tool_name}")
    logger.debug(f"Tool arguments: {arguments}")
    logger.debug(f"Tool result: {result}")


def log_error(logger: logging.Logger, error: Exception, context: str = ""):
    """Log an error with full traceback."""
    logger.error(f"Error in {context}: {str(error)}", exc_info=True)


# Auto-setup logging when module is imported
_logging_setup_done = False

def ensure_logging_setup():
    """Ensure logging is set up at least once."""
    global _logging_setup_done
    if not _logging_setup_done:
        setup_logging()
        _logging_setup_done = True
