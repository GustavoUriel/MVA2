from app import create_app, db
import json

app = create_app()

with app.test_client() as client:
  # Attempt to call the endpoint without login
  resp = client.post('/api/v1/uploads/import-default-taxonomy')
  print('Status code:', resp.status_code)
  try:
    print('JSON:', resp.get_json())
  except Exception as e:
    print('Response data:', resp.data.decode())
