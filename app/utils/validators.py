"""
Data validation utilities for MVA2 application

Provides validation functions for patient data, taxonomy data, and analysis parameters.
"""

from datetime import datetime
import re


def validate_patient_data(data):
  """
  Validate patient data before database insertion

  Args:
      data (dict): Patient data to validate

  Returns:
      list: List of validation errors, empty if valid
  """
  errors = []

  # Required fields
  if not data.get('patient_id'):
    errors.append("Patient ID is required")
  elif not isinstance(data['patient_id'], str) or len(data['patient_id'].strip()) == 0:
    errors.append("Patient ID must be a non-empty string")

  # Age validation
  if 'age' in data and data['age'] is not None:
    try:
      age = int(data['age'])
      if age < 0 or age > 120:
        errors.append("Age must be between 0 and 120")
    except (ValueError, TypeError):
      errors.append("Age must be a valid integer")

  # Sex validation
  if 'sex' in data and data['sex'] is not None:
    valid_sex = ['M', 'F', 'Male', 'Female', 'male', 'female', 'Other']
    if data['sex'] not in valid_sex:
      errors.append("Sex must be one of: M, F, Male, Female, Other")

  # Survival status validation
  if 'survival_status' in data and data['survival_status'] is not None:
    try:
      status = int(data['survival_status'])
      if status not in [0, 1]:
        errors.append("Survival status must be 0 (alive) or 1 (dead)")
    except (ValueError, TypeError):
      errors.append("Survival status must be 0 or 1")

  # Survival months validation
  if 'survival_months' in data and data['survival_months'] is not None:
    try:
      months = float(data['survival_months'])
      if months < 0:
        errors.append("Survival months cannot be negative")
    except (ValueError, TypeError):
      errors.append("Survival months must be a valid number")

  # Date validation
  if 'diagnosis_date' in data and data['diagnosis_date'] is not None:
    if isinstance(data['diagnosis_date'], str):
      try:
        datetime.fromisoformat(data['diagnosis_date'].replace('Z', '+00:00'))
      except ValueError:
        errors.append("Diagnosis date must be a valid ISO format date")

  return errors


def validate_taxonomy_data(data):
  """
  Validate taxonomy data before database insertion

  Args:
      data (dict): Taxonomy data to validate

  Returns:
      list: List of validation errors, empty if valid
  """
  errors = []

  # Required fields
  if not data.get('taxonomy_id'):
    errors.append("Taxonomy ID is required")

  # Abundance validation
  abundance_fields = ['total_abundance',
                      'max_abundance', 'min_abundance', 'mean_abundance']
  for field in abundance_fields:
    if field in data and data[field] is not None:
      try:
        value = float(data[field])
        if value < 0:
          errors.append(f"{field} cannot be negative")
      except (ValueError, TypeError):
        errors.append(f"{field} must be a valid number")

  # Prevalence validation
  if 'prevalence' in data and data['prevalence'] is not None:
    try:
      prevalence = float(data['prevalence'])
      if prevalence < 0 or prevalence > 1:
        errors.append("Prevalence must be between 0 and 1")
    except (ValueError, TypeError):
      errors.append("Prevalence must be a valid number between 0 and 1")

  # Confidence score validation
  if 'classification_confidence' in data and data['classification_confidence'] is not None:
    try:
      confidence = float(data['classification_confidence'])
      if confidence < 0 or confidence > 1:
        errors.append("Classification confidence must be between 0 and 1")
    except (ValueError, TypeError):
      errors.append("Classification confidence must be a valid number")

  return errors


def validate_analysis_config(analysis_type, config):
  """
  Validate analysis configuration parameters

  Args:
      analysis_type (str): Type of analysis
      config (dict): Analysis configuration

  Returns:
      list: List of validation errors, empty if valid
  """
  errors = []

  if analysis_type == 'cox_regression':
    # Alpha validation
    if 'alpha' in config:
      try:
        alpha = float(config['alpha'])
        if alpha <= 0 or alpha >= 1:
          errors.append("Alpha must be between 0 and 1")
      except (ValueError, TypeError):
        errors.append("Alpha must be a valid number")

    # Penalizer validation
    if 'penalizer' in config:
      try:
        penalizer = float(config['penalizer'])
        if penalizer < 0:
          errors.append("Penalizer must be non-negative")
      except (ValueError, TypeError):
        errors.append("Penalizer must be a valid number")

  elif analysis_type == 'survival':
    # Time column validation
    if not config.get('time_column'):
      errors.append("Time column is required for survival analysis")

    # Event column validation
    if not config.get('event_column'):
      errors.append("Event column is required for survival analysis")

  elif analysis_type == 'correlation':
    # Method validation
    valid_methods = ['pearson', 'spearman', 'kendall']
    if 'method' in config and config['method'] not in valid_methods:
      errors.append(
          f"Correlation method must be one of: {', '.join(valid_methods)}")

  return errors


def validate_file_upload(file, allowed_extensions):
  """
  Validate uploaded file

  Args:
      file: File object from request
      allowed_extensions (list): List of allowed file extensions

  Returns:
      list: List of validation errors, empty if valid
  """
  errors = []

  if not file:
    errors.append("No file provided")
    return errors

  if file.filename == '':
    errors.append("No file selected")
    return errors

  # Check file extension
  if '.' not in file.filename:
    errors.append("File must have an extension")
  else:
    extension = file.filename.rsplit('.', 1)[1].lower()
    if extension not in allowed_extensions:
      errors.append(
          f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}")

  return errors


def validate_email(email):
  """
  Validate email address format

  Args:
      email (str): Email address to validate

  Returns:
      bool: True if valid, False otherwise
  """
  if not email:
    return False

  pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
  return re.match(pattern, email) is not None


def validate_password(password):
  """
  Validate password strength

  Args:
      password (str): Password to validate

  Returns:
      list: List of validation errors, empty if valid
  """
  errors = []

  if not password:
    errors.append("Password is required")
    return errors

  if len(password) < 8:
    errors.append("Password must be at least 8 characters long")

  if not re.search(r'[A-Z]', password):
    errors.append("Password must contain at least one uppercase letter")

  if not re.search(r'[a-z]', password):
    errors.append("Password must contain at least one lowercase letter")

  if not re.search(r'\d', password):
    errors.append("Password must contain at least one digit")

  if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
    errors.append("Password must contain at least one special character")

  return errors


def sanitize_input(input_string):
  """
  Sanitize user input to prevent XSS and injection attacks

  Args:
      input_string (str): Input to sanitize

  Returns:
      str: Sanitized input
  """
  if not isinstance(input_string, str):
    return input_string

  # Remove potentially dangerous characters
  input_string = re.sub(r'[<>"\']', '', input_string)

  # Strip whitespace
  input_string = input_string.strip()

  return input_string


def validate_numeric_range(value, min_val=None, max_val=None, field_name="Value"):
  """
  Validate that a numeric value is within specified range

  Args:
      value: Value to validate
      min_val: Minimum allowed value
      max_val: Maximum allowed value
      field_name: Name of field for error messages

  Returns:
      list: List of validation errors, empty if valid
  """
  errors = []

  try:
    num_value = float(value)

    if min_val is not None and num_value < min_val:
      errors.append(f"{field_name} must be at least {min_val}")

    if max_val is not None and num_value > max_val:
      errors.append(f"{field_name} must be at most {max_val}")

  except (ValueError, TypeError):
    errors.append(f"{field_name} must be a valid number")

  return errors
