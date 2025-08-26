from app import create_app, db
from app.models.user import User
import os

app = create_app()
app.config['DEBUG'] = True

with app.app_context():
  # Ensure tables exist (safe in development)
  try:
    db.create_all()
  except Exception:
    pass

  # Create or get test user
  test_email = os.environ.get('TEST_USER_EMAIL', 'test_local@example.com')
  user = User.query.filter_by(email=test_email).first()
  if not user:
    user = User(email=test_email, username='test_local')
    user.set_password('testpassword')
    db.session.add(user)
    db.session.commit()

  # Use test client and perform dev login via API helper
  with app.test_client() as client:
    login_resp = client.post('/api/v1/auth/dev/login-as',
                             json={'email': test_email})
    print('Dev login status:', login_resp.status_code, login_resp.get_json())

    resp = client.post('/api/v1/uploads/import-default-taxonomy')
    print('Status code:', resp.status_code)
    try:
      print('JSON:', resp.get_json())
    except Exception as e:
      print('Response data:', resp.data.decode())
