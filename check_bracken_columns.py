import pandas as pd
df = pd.read_csv('instance/bracken.csv', sep=';')
print('First 10 columns:')
for i, col in enumerate(df.columns[:10]):
  print(f'{i}: "{col}"')
print()
print('Sample column endings:')
for col in df.columns[1:6]:
  print(f'Column: "{col}" - ends with: "{col[-5:]}"')
