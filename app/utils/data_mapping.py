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
  # Normalize keys to lowercase and map CSV column names to model attribute names
  if not taxonomy_data:
    return {}

  mapped = {}

  # Helper to clean string values
  def _clean(v):
    if v is None:
      return None
    if isinstance(v, str):
      v = v.strip()
      # remove surrounding single or double quotes often produced in CSVs
      if (v.startswith("'") and v.endswith("'")) or (v.startswith('"') and v.endswith('"')):
        v = v[1:-1].strip()
      return v if v != '' else None
    return v

  # Desired model fields
  allowed = {
      'taxonomy_id', 'asv', 'domain', 'phylum', 'class_name', 'order',
      'family', 'genus', 'species', 'full_taxonomy', 'classification_confidence'
  }

  for raw_k, raw_v in taxonomy_data.items():
    if raw_k is None:
      continue
    k = str(raw_k).lower().strip()
    v = _clean(raw_v)

    # Map common CSV column names to model attribute names
    if k == 'class':
      mapped_key = 'class_name'
    elif k == 'taxonomy':
      # keep original taxonomy id if present; map human-readable taxonomy to full_taxonomy
      mapped_key = 'full_taxonomy'
    else:
      mapped_key = k

    # Only keep keys that the model expects; allow taxonomy_id and others
    if mapped_key in allowed or mapped_key == 'taxonomy_id':
      mapped[mapped_key] = v

  return mapped
