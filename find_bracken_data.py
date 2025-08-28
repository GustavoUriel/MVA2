#!/usr/bin/env python3
"""
Check for actual numeric data in the Bracken CSV
"""

from config import BRACKEN_TIME_POINTS
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.abspath('.'))


def find_numeric_data():
  """Find rows with actual numeric data"""

  print("=== Looking for numeric data in Bracken CSV ===")

  try:
    df = pd.read_csv('instance/bracken.csv', sep=';')
    print(f"Loaded CSV with {len(df)} rows and {len(df.columns)} columns")

    # Get sample columns for each timepoint
    suffixes = [cfg['suffix'] for cfg in BRACKEN_TIME_POINTS.values()]
    sample_columns = []

    for col in df.columns[1:10]:  # Check first 10 data columns
      col_stripped = col.strip()
      for suffix in suffixes:
        if col_stripped.endswith(suffix):
          sample_columns.append(col)
          break

    print(f"Testing columns: {sample_columns}")

    # Look for rows with numeric data
    rows_with_data = 0
    for i, row in df.iterrows():
      has_numeric = False
      for col in sample_columns:
        value = row[col]
        if pd.notna(value) and str(value).strip() not in ['-', '']:
          try:
            float(value)
            has_numeric = True
            break
          except (ValueError, TypeError):
            pass

      if has_numeric:
        rows_with_data += 1
        if rows_with_data <= 5:  # Show first 5 rows with data
          taxonomy_id = str(row.iloc[0]).strip()
          print(f"\nRow {i+1}: Taxonomy ID = '{taxonomy_id}'")
          for col in sample_columns[:5]:
            value = row[col]
            if pd.notna(value) and str(value).strip() not in ['-', '']:
              try:
                float_val = float(value)
                print(f"  {col.strip()}: {float_val}")
              except (ValueError, TypeError):
                print(f"  {col.strip()}: '{value}' (not numeric)")

    print(
        f"\nFound {rows_with_data} rows with numeric data out of {len(df)} total rows")

    # Also check the overall data distribution
    print(f"\nData distribution analysis:")
    for col in sample_columns[:3]:
      print(f"\nColumn '{col.strip()}':")
      non_null = df[col].notna()
      non_dash = df[col] != '-'
      non_empty = df[col].astype(str).str.strip() != ''
      valid_mask = non_null & non_dash & non_empty

      print(f"  Total values: {len(df)}")
      print(f"  Non-null: {non_null.sum()}")
      print(f"  Non-dash: {non_dash.sum()}")
      print(f"  Non-empty: {non_empty.sum()}")
      print(f"  Valid (all conditions): {valid_mask.sum()}")

      if valid_mask.sum() > 0:
        sample_values = df[col][valid_mask].head(5)
        print(f"  Sample values: {list(sample_values)}")

  except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()


if __name__ == '__main__':
  find_numeric_data()
