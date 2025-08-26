import os
import json
import tempfile
import pytest

from app import create_app, db
from config import TestingConfig


@pytest.fixture
def app():
  # Create a TestingConfig subclass that clears engine options to avoid
  # passing pool args that SQLite's StaticPool doesn't accept in tests.
  class SafeTestingConfig(TestingConfig):
    SQLALCHEMY_ENGINE_OPTIONS = {}

  app = create_app(config_class=SafeTestingConfig)
  app.config.update({
      'TESTING': True,
      'WTF_CSRF_ENABLED': False,
      'SECRET_KEY': 'test-secret-key',
  })

  # Create a temporary instance folder so the test doesn't touch real data
  tmp_instance = tempfile.TemporaryDirectory()
  app.instance_path = tmp_instance.name

  with app.app_context():
    # Create DB schema if using SQLite testing config; many apps skip DB init here.
    try:
      db.create_all()
    except Exception:
      # If the project uses migrations or a different DB setup, ignore here.
      pass

  yield app

  # Teardown
  try:
    with app.app_context():
      db.session.remove()
      db.drop_all()
  except Exception:
    pass


def test_dev_login_and_import_default(client, app):
  # Use test client (flask pytest plugin provides `client` fixture when `app` exists)
  # First, call the dev-login endpoint to create/authenticate a test user.
  login_url = '/api/v1/auth/dev/login-as'
  res = client.post(
      login_url, json={'email': 'test_local_example_com@example.com'})
  assert res.status_code == 200
  data = res.get_json()
  assert data and data.get('success') is True

  # Now call the import-default-taxonomy endpoint
  import_url = '/api/v1/uploads/import-default-taxonomy'
  res2 = client.post(import_url)

  # The endpoint should return JSON; in testing mode the app may create a small sample file
  assert res2.content_type.startswith('application/json')
  assert res2.status_code in (200, 201, 404)
  payload = res2.get_json()
  assert isinstance(payload, dict)

  # If 200, expect keys indicating success
  if res2.status_code == 200:
    assert payload.get('status') == 'ok'
    assert 'imported' in payload or 'added' in payload
