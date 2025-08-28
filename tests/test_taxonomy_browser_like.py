import tempfile
import re
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
  tmp_instance = tempfile.TemporaryDirectory()
  app.instance_path = tmp_instance.name
  with app.app_context():
    try:
      db.create_all()
    except Exception:
      pass
  return app


def test_browser_like_flow_follows_redirects_and_returns_json():
  app = make_test_app()
  with app.test_client() as client:
    # login
    login_url = '/api/v1/auth/dev/login-as'
    r = client.post(login_url, json={'email': 'browser_user@example.com'})
    assert r.status_code == 200

    # fetch the taxonomy page HTML as a browser would
    page = client.get('/taxonomy')
    assert page.status_code == 200
    html = page.get_data(as_text=True)

    # ensure the page's JS references the taxonomy API with the expected fetch pattern
    assert re.search(r"fetch\('/api/v1/taxonomy", html)

    # Now simulate the browser fetch that omits the trailing slash (client-side code uses `/api/v1/taxonomy?${q}`)
    resp = client.get('/api/v1/taxonomy?page=1&per_page=10',
                      follow_redirects=True)
    # After following redirects, should get JSON and 200
    assert resp.status_code == 200
    assert resp.content_type.startswith('application/json')
    payload = resp.get_json()
    assert isinstance(payload, dict)
    for key in ('taxonomies', 'total_count', 'page', 'per_page', 'pages'):
      assert key in payload
