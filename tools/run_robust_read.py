from app.api.uploads import _read_csv_with_fallback_to_line_split, _robust_read_csv, _detect_csv_delimiter
import sys
import os
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

path = r"instance\\taxonomy.csv"
print('Detect delim:', _detect_csv_delimiter(path))
try:
  df = _robust_read_csv(path)
  print('robust read shape', df.shape)
  print('columns', list(df.columns))
  print('first row', df.head(1).to_dict(orient='records'))
except Exception as e:
  print('robust read failed', e)
  df2 = _read_csv_with_fallback_to_line_split(path)
  print('fallback shape', df2.shape)
  print('columns', list(df2.columns))
  print('first row', df2.head(1).to_dict(orient='records'))

print('\nForcing fallback reader now:')
df_fb = _read_csv_with_fallback_to_line_split(path)
print('fallback shape', df_fb.shape)
print('columns', list(df_fb.columns))
print('first 3 rows', df_fb.head(3).to_dict(orient='records'))
