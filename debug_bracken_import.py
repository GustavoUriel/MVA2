#!/usr/bin/env python3
"""
Debug script to test Bracken import logic step by step
"""

from config import BRACKEN_TIME_POINTS
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.abspath('.'))


def debug_bracken_import():
  """Debug the Bracken import process"""

  print("=== Debugging Bracken Import ===")

  # Load the Bracken CSV file
  try:
    df = pd.read_csv('instance/bracken.csv', sep=';')
    print(
        f"✓ Successfully loaded CSV with {len(df)} rows and {len(df.columns)} columns")

    # Check the first few columns
    print(f"First 10 columns: {list(df.columns[:10])}")
    print(f"Sample data from first row:")
    for i, col in enumerate(df.columns[:5]):
      print(f"  {col}: {df.iloc[0, i]}")

    # Check timepoint configuration
    print(f"\nTimepoint configuration from BRACKEN_TIME_POINTS:")
    for tp_key, tp_config in BRACKEN_TIME_POINTS.items():
      print(f"  {tp_key}: suffix='{tp_config['suffix']}'")

    # Analyze columns for timepoint matches
    suffixes = [cfg['suffix'] for cfg in BRACKEN_TIME_POINTS.values()]
    print(f"\nLooking for suffixes: {suffixes}")

    matching_columns = {}
    for suffix in suffixes:
      matching_columns[suffix] = []

    for col in df.columns[1:]:  # Skip first column (taxonomy)
      col_stripped = col.strip()
      for suffix in suffixes:
        if col_stripped.endswith(suffix):
          matching_columns[suffix].append(col_stripped)
          break

    print(f"\nColumn analysis:")
    total_matches = 0
    for suffix, matches in matching_columns.items():
      print(f"  Suffix '{suffix}': {len(matches)} matches")
      if matches:
        print(f"    Examples: {matches[:3]}")
      total_matches += len(matches)

    print(f"\nTotal matching columns: {total_matches}")

    # Test parsing patient IDs
    print(f"\nTesting patient ID extraction:")
    sample_columns = []
    for suffix, matches in matching_columns.items():
      if matches:
        sample_columns.extend(matches[:2])  # Take 2 examples per suffix

    for col in sample_columns[:10]:
      for tp_key, tp_config in BRACKEN_TIME_POINTS.items():
        suffix = tp_config['suffix']
        if col.endswith(suffix):
          patient_id = col[:-len(suffix)]
          print(f"  '{col}' -> Patient ID: '{patient_id}', Timepoint: '{tp_key}'")
          break

    # Test data values
    print(f"\nTesting data values from first few rows:")
    for i in range(min(3, len(df))):
      row = df.iloc[i]
      taxonomy_id = row.iloc[0]  # First column is taxonomy
      print(f"  Row {i+1}: Taxonomy ID = '{taxonomy_id}'")

      valid_values = 0
      for col in sample_columns[:5]:
        if col in df.columns:
          value = row[col]
          if pd.isna(value) or str(value).strip() in ['-', '']:
            print(f"    {col}: SKIP (empty/dash)")
          else:
            try:
              float_val = float(value)
              print(f"    {col}: {float_val}")
              valid_values += 1
            except (ValueError, TypeError):
              print(f"    {col}: SKIP (not numeric: '{value}')")
      print(f"    Valid numeric values: {valid_values}")

  except Exception as e:
    print(f"✗ Error loading or processing CSV: {e}")
    import traceback
    traceback.print_exc()


if __name__ == '__main__':
  debug_bracken_import()
