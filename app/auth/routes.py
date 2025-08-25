"""
Authentication routes for MVA2 application
"""

import traceback
from flask import render_template, redirect, url_for, flash, request, session, current_app, make_response
from flask_login import login_user, logout_user, current_user
from . import bp
from ..models.user import User
from .. import db
from ..utils.logging_utils import log_function, log_auth, user_logger


@bp.route('/login')
@log_function('auth')
def login():
  """Login page"""
  if current_user.is_authenticated:
    log_auth('LOGIN_PAGE_VISITED', current_user.email, True, 'Already authenticated, redirected to dashboard')
    return redirect(url_for('main.dashboard'))
  
  log_auth('LOGIN_PAGE_VISITED', request.remote_addr, True, 'Login page accessed')
  return render_template('auth/login.html')


@bp.route('/logout')
@log_function('auth')
def logout():
  """Logout user"""
  try:
    if current_user.is_authenticated:
      user_email = current_user.email
      log_auth('LOGOUT_INITIATED', user_email, True, f'IP: {request.remote_addr}')

      # Clear Flask-Login session
      logout_user()

      # Clear all session data
      session.clear()

      log_auth('LOGOUT_COMPLETED', user_email, True, 'Session cleared successfully')

      # Show logout page that handles Google logout and redirect
      response = make_response(render_template('logout.html'))
      response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
      response.headers['Pragma'] = 'no-cache'
      response.headers['Expires'] = '0'

      return response
    else:
      # User wasn't logged in, redirect directly to home
      log_auth('LOGOUT_ATTEMPTED', request.remote_addr, False, 'User not authenticated')
      response = make_response(redirect(url_for('main.index')))
      response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
      response.headers['Pragma'] = 'no-cache'
      response.headers['Expires'] = '0'
      return response
  except Exception as e:
    user_email = current_user.email if current_user.is_authenticated else 'unknown'
    log_auth('LOGOUT_ERROR', user_email, False, f'Error: {str(e)}')
    user_logger.log_error('auth', e, 'Logout process')
    flash('Error during logout.', 'error')
    return redirect(url_for('main.index'))


@bp.route('/force-logout')
def force_logout():
  """Force logout - clears everything and redirects to home"""
  try:
    # Clear Flask-Login session regardless of authentication state
    logout_user()

    # Clear all session data
    session.clear()

    current_app.logger.info("Force logout executed")

    # Redirect to home with cache busting
    response = make_response(redirect(url_for('main.index')))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.set_cookie('session', '', expires=0)  # Clear session cookie

    return response
  except Exception as e:
    traceback.print_exc()  # This prints the full traceback
    current_app.logger.error(f"Force logout error: {e}")
    return redirect(url_for('main.index'))


@bp.route('/google')
@log_function('auth')
def google_auth():
  """Google OAuth authentication"""
  try:
    log_auth('GOOGLE_AUTH_INITIATED', request.remote_addr, True, f'IP: {request.remote_addr}')
    
    # Get OAuth from current app extensions
    oauth = current_app.extensions.get('authlib.integrations.flask_client')
    if not oauth:
      log_auth('GOOGLE_AUTH_CONFIG_ERROR', request.remote_addr, False, 'OAuth not properly configured')
      flash('OAuth not properly configured', 'error')
      return redirect(url_for('main.index'))

    google = oauth._clients.get('google')
    if not google:
      log_auth('GOOGLE_AUTH_CONFIG_ERROR', request.remote_addr, False, 'Google OAuth client not configured')
      flash('Google OAuth client not configured', 'error')
      return redirect(url_for('main.index'))

    # Generate redirect URI using the configured endpoint
    redirect_uri = url_for('auth.login_authorized', _external=True)

    log_auth('GOOGLE_AUTH_REDIRECT', request.remote_addr, True, f'Redirect URI: {redirect_uri}')

    # Redirect to Google OAuth
    return google.authorize_redirect(redirect_uri)

  except Exception as e:
    log_auth('GOOGLE_AUTH_ERROR', request.remote_addr, False, f'Error: {str(e)}')
    user_logger.log_error('auth', e, 'Google OAuth initiation')
    flash(f'Google authentication error: {str(e)}', 'error')
    return redirect(url_for('main.index'))


@bp.route('/login/authorized')
@log_function('auth')
def login_authorized():
  """Google OAuth callback"""

  try:
    log_auth('GOOGLE_CALLBACK_RECEIVED', request.remote_addr, True, f'IP: {request.remote_addr}')
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
      log_auth('GOOGLE_TOKEN_ERROR', request.remote_addr, False, 'No token returned from Google')
      raise RuntimeError('No token returned from Google')

    log_auth('GOOGLE_TOKEN_RECEIVED', request.remote_addr, True, f"Token keys: {list(token.keys())}")

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
      traceback.print_exc()  # This prints the full traceback
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
        traceback.print_exc()  # This prints the full traceback
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
      log_auth('USER_CREATION', user_info['email'], True, f"New user from Google: {user_info.get('name')}")
      user = User.create_from_google(user_info)
    else:
      # Update existing user fields
      log_auth('USER_UPDATE', user_info['email'], True, f"Updating existing user: {user.username}")
      user.first_name = user_info.get('given_name') or user.first_name
      user.last_name = user_info.get('family_name') or user.last_name
      user.profile_picture_url = user_info.get(
          'picture') or user.profile_picture_url
      user.google_id = user_info.get('sub') or user.google_id
      user.is_verified = bool(user_info.get('email_verified'))
      db.session.commit()

    # Log in the user
    login_user(user, remember=True)
    log_auth('LOGIN_SUCCESS', user.email, True, f"IP: {request.remote_addr}, Role: {user.role}")
    
    # Update last_login timestamp
    try:
      from datetime import datetime
      user.last_login = datetime.utcnow()
      db.session.commit()
    except Exception as e2:
      log_auth('LOGIN_TIMESTAMP_ERROR', user.email, False, f"Failed updating last_login: {str(e2)}")
      user_logger.log_error('auth', e2, 'Login timestamp update')
    
    flash('Logged in successfully.', 'success')
    return redirect(url_for('main.dashboard'))
  except Exception as e:
    email = user_info.get('email') if 'user_info' in locals() else 'unknown'
    log_auth('LOGIN_FAILED', email, False, f"OAuth callback error: {str(e)}")
    user_logger.log_error('auth', e, 'Google OAuth callback')
    flash('Authentication failed.', 'error')
    return redirect(url_for('main.index'))
