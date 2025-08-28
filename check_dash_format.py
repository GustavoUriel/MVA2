#!/usr/bin/env python3
"""
Check the exact format of dash values in the CSV
"""

import pandas as pd
import sys
import os
sys.path.insert(0, os.path.abspath('.'))


def check_dash_format():
  """Check the exact format of dash values"""

  print("=== Checking dash value formats ===")

  try:
    df = pd.read_csv('instance/bracken.csv', sep=';')

    # Get a sample column
    sample_col = df.columns[1]  # First data column
    print(f"Checking column: '{sample_col}'")

    # Look at the first 10 values
    print(f"\nFirst 10 values (with repr to show exact format):")
    for i in range(10):
      value = df.iloc[i][sample_col]
      print(
          f"  Row {i+1}: {repr(value)} -> stripped: {repr(str(value).strip())}")

    # Look for different patterns
    unique_values = df[sample_col].value_counts().head(10)
    print(f"\nMost common values in {sample_col}:")
    for val, count in unique_values.items():
      print(
          f"  {repr(val)}: {count} occurrences -> stripped: {repr(str(val).strip())}")

    # Test the filtering logic
    print(f"\nTesting filtering logic:")
    test_values = [' -   ', '-', '  -  ', '0.5', ' 2.5 ', '']
    for val in test_values:
      is_empty = pd.isna(val) or str(val).strip() in ['-', '']
      print(
          f"  {repr(val)} -> is_empty: {is_empty}, stripped: {repr(str(val).strip())}")

  except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()


if __name__ == '__main__':
  check_dash_format()
