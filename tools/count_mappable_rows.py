from app.utils.data_mapping import map_taxonomy_columns
from app.api.uploads import _read_csv_with_fallback_to_line_split
import sys
import os
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

path = r"instance\\taxonomy.csv"
df = _read_csv_with_fallback_to_line_split(path)
count = 0
missing_taxid = 0
for i, row in df.iterrows():
  mapped = map_taxonomy_columns(row.to_dict())
  if mapped.get('taxonomy_id'):
    count += 1
  else:
    missing_taxid += 1
print('total rows', len(df))
print('rows with taxonomy_id', count)
print('rows missing taxonomy_id', missing_taxid)
