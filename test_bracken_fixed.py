#!/usr/bin/env python3
"""
Test the fixed Bracken import functionality
"""

import pandas as pd
from app.api.uploads import _detect_file_type
import sys
import os
sys.path.insert(0, os.path.abspath('.'))


def test_bracken_detection():
  """Test that Bracken detection now works with whitespace columns"""

  # Test the detection on the actual file
  try:
    file_type = _detect_file_type('instance/bracken.csv')
    print(f"File type detected: {file_type}")

    # Also test column analysis
    df = pd.read_csv('instance/bracken.csv', sep=';', nrows=5)
    print(f"Total columns: {len(df.columns)}")
    print(f"First 10 columns: {list(df.columns[:10])}")
    print(f"Sample columns with possible suffixes:")

    from config import BRACKEN_TIME_POINTS
    suffixes = [cfg['suffix'] for cfg in BRACKEN_TIME_POINTS.values()]
    print(f"Looking for suffixes: {suffixes}")

    matching_cols = []
    for col in df.columns:
      col_stripped = col.strip()
      for suffix in suffixes:
        if col_stripped.endswith(suffix):
          matching_cols.append(
              f"'{col}' -> '{col_stripped}' (ends with {suffix})")
          break

    print(f"Found {len(matching_cols)} matching columns:")
    for match in matching_cols[:10]:  # Show first 10
      print(f"  {match}")

    if len(matching_cols) > 10:
      print(f"  ... and {len(matching_cols) - 10} more")

  except Exception as e:
    print(f"Error testing Bracken detection: {e}")
    import traceback
    traceback.print_exc()


if __name__ == '__main__':
  test_bracken_detection()
