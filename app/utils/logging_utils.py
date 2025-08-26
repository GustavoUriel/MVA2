"""
User-specific logging utilities for MVA2 application.

This module provides a UserLogger that writes per-user, per-component
log files inside the user's folder under the Flask instance path. It
also exposes decorators and small shim functions used throughout the
codebase for consistent logging.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
import functools
from datetime import datetime
from typing import Optional, Dict, Any
from flask import current_app
from flask_login import current_user
import re
import json
import html as _html

# Small icons per component to make logs easier to scan
ICON_MAP = {
    'main': 'ℹ️',
    'auth': '🔐',
    'upload': '📤',
    'analysis': '📊',
    'data_transform': '🔧',
    'user_events': '👤',
    'errors': '❗',
    'api': '🌐',
    'taxonomy': '🧬',
    'patients': '🧾'
}


def _strip_html(text: str) -> str:
  if text is None:
    return ''
  # Unescape HTML entities then remove tags
  try:
    t = _html.unescape(str(text))
  except Exception:
    t = str(text)
  # Remove tags
  t = re.sub(r'<[^>]+>', '', t)
  # Replace newlines and collapse whitespace
  t = re.sub(r'\s+', ' ', t).strip()
  return t


def _format_details(details: dict, max_len: int = 1000) -> str:
  if not details:
    return ''
  try:
    s = json.dumps(details, default=str, separators=(',', ':'))
  except Exception:
    s = str(details)
  s = _strip_html(s)
  if len(s) > max_len:
    s = s[:max_len] + '...'
  return s


def _format_message(component: str, message: str, **details) -> str:
  icon = ICON_MAP.get(component, '')
  msg = f"{icon} {message}" if icon else message
  det = _format_details(details)
  if det:
    msg = f"{msg} | {det}"
  # Ensure single-line and reasonable length
  msg = _strip_html(msg)
  max_len = None
  try:
    max_len = int(current_app.config.get('LOG_MAX_ENTRY_LENGTH', 2000))
  except Exception:
    max_len = 2000
  if max_len and len(msg) > max_len:
    msg = msg[:max_len] + '...'
  return msg


class UserLogger:
  """User-specific logger with separate files for different process types."""

  LOG_TYPES = {
      'main': 'General application activities',
      'auth': 'Authentication events (login/logout/failures)',
      'upload': 'Data upload and file processing',
      'analysis_cox': 'Cox proportional hazards analysis',
      'analysis_kaplan': 'Kaplan-Meier survival analysis',
      'analysis_rmst': 'Restricted Mean Survival Time analysis',
      'analysis_stats': 'Statistical tests and correlations',
      'analysis_pca': 'PCA and multivariate analysis',
      'analysis_diff': 'Differential abundance analysis',
      'data_transform': 'Data transformations and processing',
      'user_events': 'User interface interactions and events',
      'errors': 'Error tracking and debugging'
  }

  def __init__(self):
    self._loggers: Dict[str, logging.Logger] = {}
    # handlers may be RotatingFileHandler or FileHandler depending on env
    self._handlers: Dict[str, logging.Handler] = {}

  def get_user_folder(self, email: Optional[str] = None) -> str:
    """Return the logs folder path for the given user email.

    Creates the folder if it does not exist.
    """
    if not email and current_user.is_authenticated:
      email = current_user.email
    elif not email:
      email = 'anonymous'

    safe_email = email.replace('@', '_').replace('.', '_')
    user_base = os.path.join(current_app.instance_path, 'users', safe_email)
    logs_folder = os.path.join(user_base, 'logs')
    os.makedirs(logs_folder, exist_ok=True)
    return logs_folder

  def get_logger(self, log_type: str, email: Optional[str] = None) -> logging.Logger:
    """Get or create a logger for the given user and component.

    The logger name is namespaced to avoid collisions.
    """
    if not email and current_user.is_authenticated:
      email = current_user.email
    elif not email:
      email = 'anonymous'

    logger_key = f"{email}_{log_type}"
    if logger_key in self._loggers:
      return self._loggers[logger_key]

    logger = logging.getLogger(f"mva2.user.{logger_key}")
    logger.setLevel(logging.DEBUG)

    # Remove existing handlers to avoid duplicate lines in long-lived processes
    if logger.handlers:
      for h in list(logger.handlers):
        try:
          logger.removeHandler(h)
        except Exception:
          pass

    # Ensure user folder exists
    user_folder = self.get_user_folder(email)

    # Build log path
    email_prefix = email.split('@')[0] if '@' in email else email
    log_filename = f"{email_prefix}_{log_type}.log"
    log_path = os.path.join(user_folder, log_filename)

    # Create rotating handler and formatter using app-configured limits
    try:
      max_bytes = int(current_app.config.get(
          'LOG_ROTATE_BYTES', 10 * 1024 * 1024))
      backup_count = int(current_app.config.get('LOG_ROTATE_BACKUP_COUNT', 5))
    except Exception:
      max_bytes = 10 * 1024 * 1024
      backup_count = 5

    handler = RotatingFileHandler(
        log_path, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8')
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(funcName)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    # Save references for cleanup
    self._loggers[logger_key] = logger
    self._handlers[logger_key] = handler

    return logger

  def close_all_handlers(self):
    """Close and remove all file handlers to avoid file locks (Windows)."""
    for key, handler in list(self._handlers.items()):
      try:
        handler.flush()
      except Exception:
        pass
      try:
        handler.close()
      except Exception:
        pass
      logger = self._loggers.get(key)
      if logger:
        try:
          logger.handlers = [h for h in logger.handlers if h is not handler]
        except Exception:
          pass

    self._handlers.clear()
    self._loggers.clear()

  # Convenience instance-level logging methods
  def log_function_entry(self, log_type: str, func_name: str, **kwargs):
    logger = self.get_logger(log_type)
    params = ', '.join(f"{k}={v}" for k, v in kwargs.items(
    ) if k.lower() not in ['password', 'token', 'secret'])
    logger.info(f"ENTER {func_name}({params})")

  def log_function_exit(self, log_type: str, func_name: str, result=None):
    logger = self.get_logger(log_type)
    if result is not None:
      logger.info(f"EXIT {func_name} -> {result}")
    else:
      logger.info(f"EXIT {func_name}")

  def log_data_transformation(self, log_type: str, operation: str,
                              input_shape=None, output_shape=None, **details):
    logger = self.get_logger(log_type)
    msg = f"DATA_TRANSFORM: {operation}"
    if input_shape:
      msg += f" | Input: {input_shape}"
    if output_shape:
      msg += f" | Output: {output_shape}"
    if details:
      msg += f" | Details: {details}"
    logger.info(msg)

  def log_user_event(self, event: str, **details):
    logger = self.get_logger('user_events')
    msg = f"USER_EVENT: {event}"
    if details:
      msg += f" | {details}"
    logger.info(msg)

  def log_error(self, log_type: str, error: Exception, context: str = None):
    logger = self.get_logger('errors')
    msg = f"ERROR in {log_type}"
    if context:
      msg += f" ({context})"
    msg += f": {type(error).__name__}: {str(error)}"
    logger.error(msg, exc_info=True)

  def log_auth_event(self, event_type: str, email: str = None,
                     success: bool = True, details: str = None):
    # Instance-level auth log
    instance_log_path = os.path.join(
        current_app.instance_path, 'auth_events.log')
    os.makedirs(os.path.dirname(instance_log_path), exist_ok=True)

    instance_logger = logging.getLogger('mva2.auth.instance')
    if not instance_logger.handlers:
      handler = logging.FileHandler(instance_log_path, encoding='utf-8')
      formatter = logging.Formatter(
          '%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
      handler.setFormatter(formatter)
      instance_logger.addHandler(handler)
      instance_logger.setLevel(logging.INFO)

    status = 'SUCCESS' if success else 'FAILED'
    msg = f"AUTH_{event_type}_{status}: {email or 'unknown'}"
    if details:
      msg += f" | {details}"

    if success:
      instance_logger.info(msg)
    else:
      instance_logger.warning(msg)

    # Also log to user-specific auth log if email provided
    if email:
      ulogger = self.get_logger('auth', email)
      if success:
        ulogger.info(f"{event_type}_{status}: {details or ''}")
      else:
        ulogger.warning(f"{event_type}_{status}: {details or ''}")


# Global logger instance
user_logger = UserLogger()


def log_function(log_type: str = 'main'):
  """Decorator to automatically log function entry and exit."""
  def decorator(func):
    # If verbose function logging is disabled via app config, return the original function
    try:
      if current_app and current_app.config.get('LOG_VERBOSE_FUNCTIONS') is False:
        return func
    except Exception:
      # If current_app is not available or config not set, proceed with decorator
      pass

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
      func_name = func.__name__
      try:
        safe_kwargs = {k: v for k, v in kwargs.items() if k.lower() not in [
            'password', 'token', 'secret']}
        user_logger.log_function_entry(log_type, func_name, **safe_kwargs)

        result = func(*args, **kwargs)

        user_logger.log_function_exit(
            log_type, func_name, result if not callable(result) else '<function>')

        return result
      except Exception as e:
        user_logger.log_error(log_type, e, f"Function: {func_name}")
        raise

    return wrapper

  return decorator


def log_data_transform(operation: str, log_type: str = 'data_transform'):
  """Decorator to log data transformation operations."""
  def decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
      try:
        input_shape = None
        if args and hasattr(args[0], 'shape'):
          input_shape = args[0].shape

        result = func(*args, **kwargs)

        output_shape = None
        if hasattr(result, 'shape'):
          output_shape = result.shape
        elif isinstance(result, (list, tuple)):
          output_shape = f"length_{len(result)}"

        user_logger.log_data_transformation(
            log_type, operation, input_shape, output_shape)

        return result
      except Exception as e:
        user_logger.log_error(log_type, e, f"Data transform: {operation}")
        raise

    return wrapper
  return decorator


def log_user_action(action: str):
  """Decorator to log user actions."""
  def decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
      try:
        user_logger.log_user_event(action)
        result = func(*args, **kwargs)
        user_logger.log_user_event(f"{action}_completed")
        return result
      except Exception as e:
        user_logger.log_error('user_events', e, f"User action: {action}")
        raise

    return wrapper
  return decorator


# Convenience functions for different log types
def log_upload_event(message: str, **details):
  logger = user_logger.get_logger('upload')
  msg = _format_message('upload', message, **details)
  logger.info(msg)


def log_analysis_event(analysis_type: str, message: str, **details):
  log_type = f"analysis_{analysis_type.lower()}"
  logger = user_logger.get_logger(log_type)
  msg = _format_message(
      'analysis', f"ANALYSIS_{analysis_type.upper()}: {message}", **details)
  logger.info(msg)


def log_auth(event_type: str, email: str = None, success: bool = True, details: str = None):
  # sanitize details
  user_logger.log_auth_event(event_type, _strip_html(
      email) if email else None, success, _strip_html(details) if details else None)


def log_step(step_name: str, status: str, component: str, **details):
  logger = user_logger.get_logger(component if component else 'main')
  msg = _format_message(component if component else 'main',
                        f"STEP {step_name} | {status}", **details)
  logger.info(msg)


def log_database_operation(action: str, table: str, component: str, **details):
  logger = user_logger.get_logger(component if component else 'main')
  msg = _format_message(component if component else 'main',
                        f"DB {action} on {table}", **details)
  logger.info(msg)


def log_file_operation(action: str, file_path: str, component: str = 'upload', **details):
  logger = user_logger.get_logger(component)
  msg = _format_message(component, f"FILE {action} {file_path}", **details)
  logger.info(msg)


def log_validation(message: str, component: str = 'main', **details):
  logger = user_logger.get_logger(component)
  msg = _format_message(component, f"VALIDATION: {message}", **details)
  logger.info(msg)


def log_api_request(method: str, endpoint: str, component: str = 'api', **details):
  logger = user_logger.get_logger(component)
  msg = _format_message(
      component, f"API_REQUEST {method} {endpoint}", **details)
  logger.info(msg)


def log_api_response(status_code: int, endpoint: str, component: str = 'api', **details):
  logger = user_logger.get_logger(component)
  msg = _format_message(
      component, f"API_RESPONSE {status_code} {endpoint}", **details)
  logger.info(msg)


def log_error(err: Exception, message: str = None, component: str = 'errors', **details):
  logger = user_logger.get_logger(component)
  base_msg = message or str(err)
  msg = _format_message('errors', f"ERROR: {base_msg}", **details)
  logger.error(msg, exc_info=True)


def log_warning(message: str, component: str = 'main', **details):
  logger = user_logger.get_logger(component)
  msg = _format_message(component, f"WARNING: {message}", **details)
  logger.warning(msg)


def log_critical(message: str, component: str = 'main', **details):
  logger = user_logger.get_logger(component)
  msg = _format_message(component, f"CRITICAL: {message}", **details)
  logger.critical(msg)
