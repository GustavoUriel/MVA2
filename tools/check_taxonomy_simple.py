import pandas as pd

path = r"instance\\taxonomy.csv"
print('Checking file:', path)

try:
  df = pd.read_csv(path, sep=',', engine='c', encoding='utf-8')
  print('Read with engine=c succeeded')
except Exception as e:
  print('engine=c failed:', e)
  df = pd.read_csv(path, sep=',', engine='python',
                   encoding='utf-8', on_bad_lines='skip')
  print('Read with engine=python fallback succeeded')

print('Columns (first 20):')
print(list(df.columns)[:20])
print('Shape:', df.shape)
print('\nFirst row as dict:')
print(df.head(1).to_dict(orient='records'))
