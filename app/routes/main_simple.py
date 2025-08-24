"""
Main web routes for MVA2 application

Handles the main web interface routes for the application.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from .. import db

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
  """Home page"""
  return render_template('base.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
  """Main dashboard"""
  try:
    return render_template('dashboard.html')
  except Exception as e:
    current_app.logger.error(f"Dashboard error: {e}")
    flash(f"Error loading dashboard: {str(e)}", 'error')
    return redirect(url_for('main.index'))


@main_bp.route('/about')
def about():
  """About page"""
  return render_template('about.html')


@main_bp.route('/contact')
def contact():
  """Contact page"""
  return render_template('contact.html')


@main_bp.route('/health')
def health():
  """Health check endpoint"""
  return jsonify({'status': 'healthy', 'message': 'MVA2 is running'})
