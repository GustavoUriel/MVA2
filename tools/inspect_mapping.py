from app.utils.data_mapping import map_taxonomy_columns
from app.api.uploads import _read_csv_with_fallback_to_line_split
import sys
import os
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

path = r"instance\\taxonomy.csv"
df = _read_csv_with_fallback_to_line_split(path)
print('df shape', df.shape)
print('columns', list(df.columns))

for i, row in df.head(10).iterrows():
  raw = row.to_dict()
  mapped = map_taxonomy_columns(raw)
  print('\nrow', i)
  print('raw keys:', list(raw.keys()))
  print('mapped keys:', list(mapped.keys()))
  for k, v in mapped.items():
    print(' ', k, ':', (v[:100] if isinstance(v, str) else v))
