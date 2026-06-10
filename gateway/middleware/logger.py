"""Gateway Request Logger — Structured Logging with File & Rotation."""

import logging
import json
from datetime import datetime
from functools import wraps
from logging.handlers import RotatingFileHandler
from flask import request, g


# Configure rotating file logger
def setup_logger(log_file="logs/gateway.log", max_bytes=10485760, backup_count=5):
    """Initialize rotating file logger for gateway requests."""
    logger = logging.getLogger("gateway")
    logger.setLevel(logging.INFO)
    
    # Create logs directory if it doesn't exist
    import os
    os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
    
    # Rotating file handler
    handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


LOGGER = setup_logger()


def log_request(req, response_status=None, response_time_ms=None):
    """
    Log incoming HTTP request with metadata.
    
    Args:
        req: Flask request object
        response_status: HTTP status code (optional)
        response_time_ms: Response time in milliseconds (optional)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    log_entry = {
        "timestamp": timestamp,
        "method": req.method,
        "path": req.path,
        "remote_addr": req.remote_addr,
        "user_agent": req.headers.get("User-Agent", "unknown"),
        "content_length": req.content_length or 0,
    }
    
    if response_status:
        log_entry["response_status"] = response_status
    
    if response_time_ms:
        log_entry["response_time_ms"] = response_time_ms
    
    log_level = "INFO"
    if response_status and response_status >= 500:
        log_level = "ERROR"
    elif response_status and response_status >= 400:
        log_level = "WARNING"
    
    # Console output
    status_str = f" → {response_status}" if response_status else ""
    time_str = f" ({response_time_ms}ms)" if response_time_ms else ""
    print(f"[GATEWAY] [{timestamp}] {req.method} {req.path}{status_str}{time_str} | {req.remote_addr}")
    
    # File logging
    getattr(LOGGER, log_level.lower())(json.dumps(log_entry))


def log_error(error_msg: str, error_detail: dict = None):
    """Log application errors with context."""
    error_entry = {
        "timestamp": datetime.now().isoformat(),
        "error": error_msg,
        "detail": error_detail or {},
    }
    LOGGER.error(json.dumps(error_entry))


def request_logging(f):
    """Decorator for automatic request/response logging."""
    @wraps(f)
    def decorated(*args, **kwargs):
        import time
        start_time = time.time()
        
        # Store start time in Flask's g object
        g.start_time = start_time
        g.request_path = request.path
        
        try:
            response = f(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000
            
            # Extract status code
            status_code = 200
            if isinstance(response, tuple):
                status_code = response[1] if len(response) > 1 else 200
            
            log_request(request, response_status=status_code, response_time_ms=round(duration_ms, 2))
            return response
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            log_error(str(e), {"path": request.path, "duration_ms": round(duration_ms, 2)})
            raise
    
    return decorated


def get_logger():
    """Get the configured logger instance."""
    return LOGGER
