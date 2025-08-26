import os
import json
from app import create_app, db
from config import TestingConfig


class SafeTestingConfig(TestingConfig):
  SQLALCHEMY_ENGINE_OPTIONS = {}
  SECRET_KEY = 'test-secret-key'


app = create_app(config_class=SafeTestingConfig)
app.testing = True

routes_to_check = [
    ('GET', '/health'),
    ('GET', '/api/v1/'),
    ('GET', '/api/v1/auth/status'),
    ('POST', '/api/v1/auth/dev/login-as'),
    ('GET', '/api/v1/patients/'),
    ('POST', '/api/v1/uploads/import-default-taxonomy'),
    ('GET', '/'),
    ('GET', '/dashboard'),
    ('GET', '/taxonomy'),
    ('GET', '/api/quick-stats'),
]

results = []
with app.test_client() as client:
  # ensure database tables exist for testing
  with app.app_context():
    try:
      db.create_all()
    except Exception:
      pass

  # unauthenticated checks
  for method, path in routes_to_check[:3]:
    func = getattr(client, method.lower())
    try:
      r = func(path)
      results.append((method, path, r.status_code, r.content_type))
    except Exception as e:
      results.append((method, path, 'EX', str(e)))

  # authenticate using dev-login
  try:
    r = client.post('/api/v1/auth/dev/login-as',
                    json={'email': 'test@example.com'})
    results.append(('POST', '/api/v1/auth/dev/login-as',
                   r.status_code, r.get_json()))
  except Exception as e:
    results.append(('POST', '/api/v1/auth/dev/login-as', 'EX', str(e)))

  # now authenticated checks
  for method, path in routes_to_check[4:]:
    func = getattr(client, method.lower())
    try:
      if method == 'POST' and path.endswith('import-default-taxonomy'):
        r = func(path)
      else:
        r = func(path)
      # Try to safely get JSON if possible
      try:
        payload = r.get_json()
      except Exception:
        payload = None
      results.append((method, path, r.status_code, payload or r.content_type))
    except Exception as e:
      results.append((method, path, 'EX', str(e)))

print('Route check results:')
for rec in results:
  print(rec)
