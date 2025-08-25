"""
User-specific logging utilities for MVA2 application.

Implements comprehensive logging system as specified in prompts.txt:
- User-specific log files named by email prefix
- Separate log files for different process types
- Function-level logging with datetime stamps
- Authentication event logging
- Data transformation and user event tracking
"""

import os
import logging
import functools
from datetime import datetime
from typing import Optional, Dict, Any
from flask import current_app, g
from flask_login import current_user


class UserLogger:
    """User-specific logger with separate files for different process types."""
    
    # Log file types and their descriptions
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
        self._handlers: Dict[str, logging.FileHandler] = {}
    
    def get_user_folder(self, email: Optional[str] = None) -> str:
        """Get user-specific folder path."""
        if not email and current_user.is_authenticated:
            email = current_user.email
        elif not email:
            email = "anonymous"
        
        safe_email = email.replace('@', '_').replace('.', '_')
        user_folder = os.path.join(current_app.instance_path, 'users', safe_email)
        os.makedirs(user_folder, exist_ok=True)
        return user_folder
    
    def get_logger(self, log_type: str, email: Optional[str] = None) -> logging.Logger:
        """Get or create a user-specific logger for the given log type."""
        if not email and current_user.is_authenticated:
            email = current_user.email
        elif not email:
            email = "anonymous"
        
        # Create unique logger key
        logger_key = f"{email}_{log_type}"
        
        if logger_key in self._loggers:
            return self._loggers[logger_key]
        
        # Create logger
        logger = logging.getLogger(f"mva2.user.{logger_key}")
        logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if logger.handlers:
            logger.handlers.clear()
        
        # Create user folder
        user_folder = self.get_user_folder(email)
        
        # Create log file path
        email_prefix = email.split('@')[0] if '@' in email else email
        log_filename = f"{email_prefix}_{log_type}.log"
        log_path = os.path.join(user_folder, log_filename)
        
        # Create file handler
        handler = logging.FileHandler(log_path, encoding='utf-8')
        handler.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(funcName)-20s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
        
        # Store references
        self._loggers[logger_key] = logger
        self._handlers[logger_key] = handler
        
        return logger
    
    def log_function_entry(self, log_type: str, func_name: str, **kwargs):
        """Log function entry with parameters."""
        logger = self.get_logger(log_type)
        params = ', '.join(f"{k}={v}" for k, v in kwargs.items() if k != 'password')
        logger.info(f"ENTER {func_name}({params})")
    
    def log_function_exit(self, log_type: str, func_name: str, result=None):
        """Log function exit with result."""
        logger = self.get_logger(log_type)
        if result is not None:
            logger.info(f"EXIT {func_name} -> {result}")
        else:
            logger.info(f"EXIT {func_name}")
    
    def log_data_transformation(self, log_type: str, operation: str, 
                              input_shape=None, output_shape=None, **details):
        """Log data transformation operations."""
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
        """Log user interface events and interactions."""
        logger = self.get_logger('user_events')
        msg = f"USER_EVENT: {event}"
        if details:
            msg += f" | {details}"
        logger.info(msg)
    
    def log_error(self, log_type: str, error: Exception, context: str = None):
        """Log errors with context."""
        logger = self.get_logger('errors')
        msg = f"ERROR in {log_type}"
        if context:
            msg += f" ({context})"
        msg += f": {type(error).__name__}: {str(error)}"
        logger.error(msg, exc_info=True)
    
    def log_auth_event(self, event_type: str, email: str = None, 
                      success: bool = True, details: str = None):
        """Log authentication events to instance-level auth log."""
        # Instance-level auth log
        instance_log_path = os.path.join(current_app.instance_path, 'auth_events.log')
        os.makedirs(os.path.dirname(instance_log_path), exist_ok=True)
        
        # Create instance logger if not exists
        instance_logger = logging.getLogger('mva2.auth.instance')
        if not instance_logger.handlers:
            handler = logging.FileHandler(instance_log_path, encoding='utf-8')
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            instance_logger.addHandler(handler)
            instance_logger.setLevel(logging.INFO)
        
        # Log to instance file
        status = "SUCCESS" if success else "FAILED"
        msg = f"AUTH_{event_type}_{status}: {email or 'unknown'}"
        if details:
            msg += f" | {details}"
        
        if success:
            instance_logger.info(msg)
        else:
            instance_logger.warning(msg)
        
        # Also log to user-specific auth log if email provided
        if email:
            user_logger = self.get_logger('auth', email)
            if success:
                user_logger.info(f"{event_type}_{status}: {details or ''}")
            else:
                user_logger.warning(f"{event_type}_{status}: {details or ''}")


# Global logger instance
user_logger = UserLogger()


def log_function(log_type: str = 'main'):
    """Decorator to automatically log function entry and exit."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Log function entry
            func_name = func.__name__
            try:
                # Filter out sensitive parameters
                safe_kwargs = {k: v for k, v in kwargs.items() 
                             if k.lower() not in ['password', 'token', 'secret']}
                user_logger.log_function_entry(log_type, func_name, **safe_kwargs)
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Log function exit
                user_logger.log_function_exit(log_type, func_name, 
                                            result if not callable(result) else '<function>')
                
                return result
                
            except Exception as e:
                # Log error
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
                # Try to get input shape from first argument (usually DataFrame)
                input_shape = None
                if args and hasattr(args[0], 'shape'):
                    input_shape = args[0].shape
                
                result = func(*args, **kwargs)
                
                # Try to get output shape
                output_shape = None
                if hasattr(result, 'shape'):
                    output_shape = result.shape
                elif isinstance(result, (list, tuple)):
                    output_shape = f"length_{len(result)}"
                
                user_logger.log_data_transformation(
                    log_type, operation, input_shape, output_shape
                )
                
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
                # Log user action
                user_logger.log_user_event(action)
                
                result = func(*args, **kwargs)
                
                # Log completion
                user_logger.log_user_event(f"{action}_completed")
                
                return result
                
            except Exception as e:
                user_logger.log_error('user_events', e, f"User action: {action}")
                raise
        
        return wrapper
    return decorator


# Convenience functions for different log types
def log_upload_event(message: str, **details):
    """Log upload-related events."""
    logger = user_logger.get_logger('upload')
    msg = f"UPLOAD: {message}"
    if details:
        msg += f" | {details}"
    logger.info(msg)


def log_analysis_event(analysis_type: str, message: str, **details):
    """Log analysis-related events."""
    log_type = f"analysis_{analysis_type.lower()}"
    logger = user_logger.get_logger(log_type)
    msg = f"ANALYSIS_{analysis_type.upper()}: {message}"
    if details:
        msg += f" | {details}"
    logger.info(msg)


def log_auth(event_type: str, email: str = None, success: bool = True, details: str = None):
    """Convenience function for authentication logging."""
    user_logger.log_auth_event(event_type, email, success, details)
