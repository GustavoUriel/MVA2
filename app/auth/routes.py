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

    # Handle the callback
    token = google.authorize_access_token()
    user_info = google.get('userinfo').json()

    # Log user info for debugging
    current_app.logger.info(f"User info: {user_info}")

    # Find or create user
    user = User.query.filter_by(email=user_info['email']).first()
    if not user:
      user = User()
      user.email = user_info['email']
      db.session.add(user)

    # Update user info
    user.username = user_info.get('name')
    user.profile_picture_url = user_info.get('picture')
    user.google_id = user_info.get('sub')
    db.session.commit()

    # Log in the user
    login_user(user)
    flash('Logged in successfully.', 'success')
    return redirect(url_for('main.dashboard'))

  except Exception as e:
    current_app.logger.error(f"Error during Google OAuth callback: {e}")
    flash('Authentication failed.', 'error')
    return redirect(url_for('main.index'))
