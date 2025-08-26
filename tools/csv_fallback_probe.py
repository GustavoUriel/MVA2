import csv
from app.utils.data_mapping import map_taxonomy_columns

path = r"instance\taxonomy.csv"
print('Reading file with csv.reader, quotechar="\'"')
with open(path, 'r', encoding='utf-8', errors='ignore') as f:
  reader = csv.reader(f, delimiter=',', quotechar="'", skipinitialspace=True)
  rows = []
  for i, row in enumerate(reader):
    rows.append(row)
    if i >= 10:
      break

print('Lines read:', len(rows))
for i, row in enumerate(rows[:5]):
  print(i, len(row), row[:10])

# Build dicts from header
header = rows[0]
print('\nHeader:', header)
print('\nSample mapped rows:')
for r in rows[1:6]:
  data = {h: (r[idx] if idx < len(r) else None) for idx, h in enumerate(header)}
  mapped = map_taxonomy_columns(data)
  print(mapped)
