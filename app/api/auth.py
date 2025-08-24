"""
Authentication API endpoints for MVA2 application

Handles user authentication, authorization, and session management.
"""

from flask import request, session, current_app, jsonify, url_for
from flask_restx import Namespace, Resource, fields
from flask_login import login_user, logout_user, login_required, current_user
from google.oauth2 import id_token
from google.auth.transport import requests
import secrets

from app.models.user import User
from app import db

auth_ns = Namespace('auth', description='Authentication operations')

# Response models
user_model = auth_ns.model('User', {
    'id': fields.Integer(description='User ID'),
    'email': fields.String(description='User email'),
    'name': fields.String(description='User full name'),
    'role': fields.String(description='User role'),
    'created_at': fields.DateTime(description='Account creation date'),
    'last_login': fields.DateTime(description='Last login date')
})

login_response = auth_ns.model('LoginResponse', {
    'success': fields.Boolean(description='Login success status'),
    'message': fields.String(description='Response message'),
    'user': fields.Nested(user_model, description='User information'),
    'redirect_url': fields.String(description='Redirect URL after login')
})

# Request models
google_auth_model = auth_ns.model('GoogleAuth', {
    'credential': fields.String(required=True, description='Google ID token'),
    'g_csrf_token': fields.String(description='CSRF token from Google')
})


@auth_ns.route('/google')
class GoogleAuth(Resource):
  """Google OAuth authentication endpoint"""

  @auth_ns.doc('google_auth')
  @auth_ns.expect(google_auth_model)
  @auth_ns.marshal_with(login_response)
  def post(self):
    """Authenticate user with Google OAuth"""
    try:
      # Get Google ID token from request
      data = request.get_json()
      if not data or 'credential' not in data:
        return {
            'success': False,
            'message': 'Google credential required'
        }, 400

      token = data['credential']

      # Verify the token
      try:
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            current_app.config['GOOGLE_CLIENT_ID']
        )

        # Verify the issuer
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
          return {
              'success': False,
              'message': 'Invalid token issuer'
          }, 400

      except ValueError as e:
        import traceback
        traceback.print_exc()  # This prints the full traceback
        current_app.logger.error(f"Token verification failed: {e}")
        return {
            'success': False,
            'message': 'Invalid Google token'
        }, 401

      # Extract user information
      email = idinfo.get('email')
      name = idinfo.get('name')
      picture = idinfo.get('picture')
      google_id = idinfo.get('sub')

      if not email:
        return {
            'success': False,
            'message': 'Email not provided by Google'
        }, 400

      # Find or create user
      user = User.query.filter_by(email=email).first()

      if not user:
        # Create new user using helper to ensure unique username
        google_user_info = {
            'email': email,
            'given_name': idinfo.get('given_name'),
            'family_name': idinfo.get('family_name'),
            'sub': google_id,
            'picture': picture,
            'email_verified': idinfo.get('email_verified', False),
            'name': name
        }
        user = User.create_from_google(google_user_info)
        current_app.logger.info(f"Created new user: {email}")
      else:
        # Update existing user information
        if name and not user.username:
          user.username = name
        user.first_name = idinfo.get('given_name') or user.first_name
        user.last_name = idinfo.get('family_name') or user.last_name
        user.google_id = google_id or user.google_id
        user.profile_picture_url = picture or user.profile_picture_url
        user.is_verified = bool(idinfo.get('email_verified'))
        # update last_login
        from datetime import datetime
        user.last_login = datetime.utcnow()
        db.session.commit()

      # Log in user
      login_user(user, remember=True)

      # Generate new session token for security
      session.permanent = True
      session['user_id'] = user.id
      session['csrf_token'] = secrets.token_hex(16)

      # Build explicit user payload matching response model
      user_name = None
      if user.first_name or user.last_name:
        user_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
      user_name = user_name or user.username or user.email

      return {
          'success': True,
          'message': 'Login successful',
          'user': {
              'id': user.id,
              'email': user.email,
              'name': user_name,
              'role': user.role,
              'created_at': user.created_at,
              'last_login': user.last_login,
          },
          'redirect_url': url_for('main.dashboard')
      }

    except Exception as e:
      import traceback
      traceback.print_exc()  # This prints the full traceback
      current_app.logger.error(f"Google auth error: {e}")
      return {
          'success': False,
          'message': 'Authentication failed'
      }, 500


@auth_ns.route('/logout')
class Logout(Resource):
  """User logout endpoint"""

  @auth_ns.doc('logout')
  @login_required
  def post(self):
    """Log out current user"""
    try:
      user_email = current_user.email
      logout_user()
      session.clear()

      current_app.logger.info(f"User logged out: {user_email}")

      return {
          'success': True,
          'message': 'Logout successful',
          'redirect_url': url_for('main.index')
      }

    except Exception as e:
      import traceback
      traceback.print_exc()  # This prints the full traceback
      current_app.logger.error(f"Logout error: {e}")
      return {
          'success': False,
          'message': 'Logout failed'
      }, 500


@auth_ns.route('/status')
class AuthStatus(Resource):
  """Authentication status endpoint"""

  @auth_ns.doc('auth_status')
  @auth_ns.marshal_with(user_model)
  def get(self):
    """Get current authentication status"""
    if current_user.is_authenticated:
      return {
          'authenticated': True,
          'user': current_user.to_dict()
      }
    else:
      return {
          'authenticated': False,
          'user': None
      }


@auth_ns.route('/profile')
class Profile(Resource):
  """User profile management"""

  @auth_ns.doc('get_profile')
  @auth_ns.marshal_with(user_model)
  @login_required
  def get(self):
    """Get current user profile"""
    return current_user.to_dict()

  @auth_ns.doc('update_profile')
  @auth_ns.expect(auth_ns.model('ProfileUpdate', {
      'name': fields.String(description='User name'),
      'preferences': fields.Raw(description='User preferences')
  }))
  @auth_ns.marshal_with(user_model)
  @login_required
  def put(self):
    """Update current user profile"""
    try:
      data = request.get_json()

      if 'name' in data:
        current_user.name = data['name']

      if 'preferences' in data:
        current_user.preferences = data['preferences']

      db.session.commit()

      return current_user.to_dict()

    except Exception as e:
      import traceback
      traceback.print_exc()  # This prints the full traceback
      current_app.logger.error(f"Profile update error: {e}")
      return {'message': 'Profile update failed'}, 500


@auth_ns.route('/session')
class SessionInfo(Resource):
  """Session information endpoint"""

  @auth_ns.doc('session_info')
  @login_required
  def get(self):
    """Get current session information"""
    return {
        'user_id': current_user.id,
        'session_id': session.get('session_id'),
        'csrf_token': session.get('csrf_token'),
        'login_time': current_user.last_login.isoformat() if current_user.last_login else None,
        'is_permanent': session.permanent
    }
