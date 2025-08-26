from app.models.taxonomy import Taxonomy
from app.utils.data_mapping import map_taxonomy_columns
from app.api.uploads import _read_csv_with_fallback_to_line_split
from app import create_app, db
import sys
import os
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

app = create_app()
app.app_context().push()


path = r"instance\\taxonomy.csv"
df = _read_csv_with_fallback_to_line_split(path)

user_id = 1
print('Existing taxonomies for user', user_id,
      Taxonomy.query.filter_by(user_id=user_id).count())

# Try creating first 5 rows
for i, row in df.head(5).iterrows():
  mapped = map_taxonomy_columns(row.to_dict())
  print('\nAttempting create for row', i, 'mapped keys:', list(mapped.keys()))
  try:
    t = Taxonomy.create_from_dict(user_id, mapped)
    print('Created taxonomy id', t.id)
  except Exception as e:
    print('Create failed:', e)

print('Final count', Taxonomy.query.filter_by(user_id=user_id).count())
