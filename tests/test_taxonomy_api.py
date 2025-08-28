import tempfile
from app import create_app, db
from config import TestingConfig


def make_test_app():
  class SafeTestingConfig(TestingConfig):
    SQLALCHEMY_ENGINE_OPTIONS = {}

  app = create_app(config_class=SafeTestingConfig)
  app.config.update({
      'TESTING': True,
      'WTF_CSRF_ENABLED': False,
      'SECRET_KEY': 'test-secret-key',
  })

  # Use a temporary instance folder so tests don't touch real data
  tmp_instance = tempfile.TemporaryDirectory()
  app.instance_path = tmp_instance.name

  with app.app_context():
    try:
      db.create_all()
    except Exception:
      pass

  return app


def test_taxonomy_endpoint_returns_pagination_and_keys():
  app = make_test_app()

  with app.test_client() as client:
    # Log in with dev login endpoint to create a test user/session
    login_url = '/api/v1/auth/dev/login-as'
    res = client.post(login_url, json={'email': 'test_user@example.com'})
    assert res.status_code == 200
    # Now call the taxonomy API (use trailing slash to avoid redirect)
    res2 = client.get('/api/v1/taxonomy/')
    # Ensure we get JSON back and a 200/401 depending on auth
    assert res2.content_type.startswith('application/json')

    # If not authorized (shouldn't happen after dev-login), show helpful info
    assert res2.status_code == 200
    payload = res2.get_json()
    assert isinstance(payload, dict)

    # Basic expected keys used by the front-end table
    for key in ('taxonomies', 'total_count', 'page', 'per_page', 'pages'):
      assert key in payload
