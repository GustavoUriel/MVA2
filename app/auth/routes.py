"""
Authentication routes for MVA2 application
"""

from flask import render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, current_user
from . import bp
from ..models.user import User
from .. import db


@bp.route('/login')
def login():
  """Login page"""
  if current_user.is_authenticated:
    return redirect(url_for('main.dashboard'))
  return render_template('auth/login.html')


@bp.route('/logout')
def logout():
  """Logout user"""
  logout_user()
  return redirect(url_for('main.index'))


@bp.route('/google')
def google_auth():
  """Google OAuth authentication"""
  try:
    # Get OAuth from current app extensions
    oauth = current_app.extensions.get('authlib.integrations.flask_client')
    if not oauth:
      flash('OAuth not properly configured', 'error')
      return redirect(url_for('main.index'))

    google = oauth._clients.get('google')
    if not google:
      flash('Google OAuth client not configured', 'error')
      return redirect(url_for('main.index'))

    # Generate redirect URI using the configured endpoint
    redirect_uri = url_for('auth.login_authorized', _external=True)

    current_app.logger.info(
        f"Initiating Google OAuth with redirect URI: {redirect_uri}")

    # Redirect to Google OAuth
    return google.authorize_redirect(redirect_uri)

  except Exception as e:
    current_app.logger.error(f"Google OAuth initiation error: {e}")
    flash(f'Google authentication error: {str(e)}', 'error')
    return redirect(url_for('main.index'))


@bp.route('/login/authorized')
def login_authorized():
  """Google OAuth callback"""

  """   try: """
  # Get OAuth from current app extensions
  oauth = current_app.extensions.get('authlib.integrations.flask_client')
  if not oauth:
    flash('OAuth not properly configured', 'error')
    return redirect(url_for('main.index'))

  google = oauth._clients.get('google')
  if not google:
    flash('Google OAuth client not configured', 'error')
    return redirect(url_for('main.index'))

  # Handle the callback
  token = google.authorize_access_token()
  if not token:
    raise RuntimeError('No token returned from Google')

  current_app.logger.info(f"Received token keys: {list(token.keys())}")

  # Prefer ID token claims (no extra HTTP request)
  user_info = None
  try:
    claims = google.parse_id_token(token)
    if claims:
      user_info = {
          'email': claims.get('email'),
          'name': claims.get('name'),
          'given_name': claims.get('given_name'),
          'family_name': claims.get('family_name'),
          'picture': claims.get('picture'),
          'sub': claims.get('sub'),
          'email_verified': claims.get('email_verified')
      }
      current_app.logger.info('Parsed ID token claims successfully')
  except Exception as parse_err:
    current_app.logger.warning(f"parse_id_token failed: {parse_err}")

  # Fallback to UserInfo endpoint if needed
  if not user_info or not user_info.get('email'):
    try:
      # Use the correct Google userinfo endpoint
      resp = google.get('https://openidconnect.googleapis.com/v1/userinfo')
      if not resp or resp.status_code >= 400:
        raise RuntimeError('Failed to fetch userinfo from Google endpoint')
      user_info = resp.json()
      current_app.logger.info('Fetched userinfo from endpoint')
    except Exception as ui_err:
      current_app.logger.error(f"Failed to fetch userinfo: {ui_err}")
      raise

  if not user_info or not user_info.get('email'):
    raise RuntimeError('Missing email in Google user info')

  # Log user info for debugging (redact picture URL length only)
  safe_info = {k: (v if k != 'picture' else '...')
               for k, v in user_info.items()}
  current_app.logger.info(f"User info (redacted): {safe_info}")

  # Find or create user
  user = User.query.filter_by(email=user_info['email']).first()
  if not user:
    # Use helper to ensure unique username and defaults
    user = User.create_from_google(user_info)
  else:
    # Update existing user fields
    user.first_name = user_info.get('given_name') or user.first_name
    user.last_name = user_info.get('family_name') or user.last_name
    user.profile_picture_url = user_info.get(
        'picture') or user.profile_picture_url
    user.google_id = user_info.get('sub') or user.google_id
    user.is_verified = bool(user_info.get('email_verified'))
    db.session.commit()

  # Log in the user
  login_user(user, remember=True)
  # Update last_login timestamp
  try:
    from datetime import datetime
    user.last_login = datetime.utcnow()
    db.session.commit()
  except Exception as e2:
    current_app.logger.warning(f"Failed updating last_login: {e2}")
  flash('Logged in successfully.', 'success')
  return redirect(url_for('main.dashboard'))


"""   except Exception as e:
    current_app.logger.error(f"Error during Google OAuth callback: {e}")
    flash('Authentication failed.', 'error')
    return redirect(url_for('main.index')) """
