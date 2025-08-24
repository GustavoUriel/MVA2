"""
Data mapping utilities for MVA2 application

Handles mapping and transformation of imported data to database models.
"""


def map_patient_columns(patient_data):
  """
  Map patient data columns to database model fields

  Args:
      patient_data (dict): Raw patient data from import

  Returns:
      dict: Mapped data ready for Patient model
  """
  # Return the data as-is for now, can be enhanced later
  return patient_data


def map_taxonomy_columns(taxonomy_data):
  """
  Map taxonomy data columns to database model fields

  Args:
      taxonomy_data (dict): Raw taxonomy data from import

  Returns:
      dict: Mapped data ready for Taxonomy model
  """
  # Return the data as-is for now, can be enhanced later
  return taxonomy_data
