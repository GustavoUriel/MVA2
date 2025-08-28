#!/usr/bin/env python3
"""
Fix the Bracken import logic by updating column handling
"""

import re


def fix_bracken_import():
  """Fix the Bracken import logic in uploads.py"""

  # Read the current file
  with open('app/api/uploads.py', 'r', encoding='utf-8') as f:
    content = f.read()

  # Pattern to find the Bracken import sections
  pattern1 = r'for col in df\.columns\[1:\]:  # Skip taxonomy column\s+if pd\.isna\(row\[col\]\) or str\(row\[col\]\)\.strip\(\) in \[\'-\', \'\'\]:\s+continue'

  replacement1 = '''for col in df.columns[1:]:  # Skip taxonomy column
                    col_stripped = col.strip()  # Strip whitespace from column name
                    if pd.isna(row[col]) or str(row[col]).strip() in ['-', '']:
                      continue'''

  # Replace the first pattern
  content = re.sub(pattern1, replacement1, content)

  # Pattern for the suffix checking
  pattern2 = r'if col\.endswith\(suffix\):\s+patient_id = col\[:-len\(suffix\)\]'
  replacement2 = '''if col_stripped.endswith(suffix):
                        patient_id = col_stripped[:-len(suffix)]'''

  # Replace all occurrences of the suffix checking
  content = re.sub(pattern2, replacement2, content)

  # Write the fixed content back
  with open('app/api/uploads.py', 'w', encoding='utf-8') as f:
    f.write(content)

  print("Fixed Bracken import logic in uploads.py")


if __name__ == '__main__':
  fix_bracken_import()
