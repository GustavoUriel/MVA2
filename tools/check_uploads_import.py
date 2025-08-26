import traceback
try:
  import app.api.uploads as uploads
  print('Imported uploads module successfully')
  # List routes registered on uploads_ns
  try:
    ns = uploads.uploads_ns
    print('uploads_ns routes:')
    for r in getattr(ns, 'resources', []):
      print('  resource:', r)
  except Exception as e:
    print('Could not list uploads_ns resources:', e)
except Exception as e:
  print('Import failed:')
  traceback.print_exc()
