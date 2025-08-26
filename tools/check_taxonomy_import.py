import pandas as pd
from app.api.uploads import _detect_csv_delimiter
from app.utils.data_mapping import map_taxonomy_columns

path = r"instance\taxonomy.csv"
print('Checking file:', path)
delim = _detect_csv_delimiter(path)
print('Detected delimiter:', repr(delim))
if delim is None:
  delim = ','

df = pd.read_csv(path, sep=delim, engine='python')
print('Columns (first 20):')
print([c for c in df.columns][:20])
print('Lowercased columns (first 20):')
print([str(c).lower() for c in df.columns][:20])

print('\nSample mapped rows (first 5):')
for i, row in df.head(5).iterrows():
  raw = row.to_dict()
  mapped = map_taxonomy_columns(raw)
  print(i, mapped)
