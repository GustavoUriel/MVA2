"""
Authentication routes for MVA2 application
"""

from flask import render_template, redirect, url_for, flash, request
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
  # OAuth implementation would go here
  flash('Google authentication not yet implemented', 'info')
  return redirect(url_for('auth.login'))
