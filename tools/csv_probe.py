import pandas as pd
from pprint import pprint
path = r"instance\taxonomy.csv"


def try_read(kwargs):
  try:
    df = pd.read_csv(path, **kwargs)
    print('SUCCESS', kwargs)
    print('shape', df.shape)
    print('columns', list(df.columns))
    print('first row', df.head(1).to_dict(orient='records'))
    return True
  except Exception as e:
    print('FAIL', kwargs, '->', e)
    return False


options = [
    {'sep': ',', 'engine': 'c'},
    {'sep': ',', 'engine': 'c', 'quotechar': "'"},
    {'sep': ',', 'engine': 'python', 'quotechar': "'"},
    {'sep': ',', 'engine': 'python'},
    {'sep': ';', 'engine': 'c'},
    {'sep': '\t', 'engine': 'c'},
]

for opt in options:
  print('\nTrying', opt)
  try_read(opt)
