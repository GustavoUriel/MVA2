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
  if current_user.is_authenticated:
    return redirect(url_for('main.dashboard'))
  return render_template('index.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
  """Main dashboard"""
  try:
    # Get counts for dashboard cards
    # TODO: Replace with actual database queries when models are implemented
    patient_count = 0
    analysis_count = 0
    taxonomy_count = 0

    return render_template('dashboard.html',
                           patient_count=patient_count,
                           analysis_count=analysis_count,
                           taxonomy_count=taxonomy_count)
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


@main_bp.route('/patients')
@login_required
def patients():
  """Patients management page"""
  try:
    # TODO: Implement patient listing logic
    return render_template('patients.html')
  except Exception as e:
    current_app.logger.error(f"Patients page error: {e}")
    flash(f"Error loading patients: {str(e)}", 'error')
    return redirect(url_for('main.dashboard'))


@main_bp.route('/taxonomy')
@login_required
def taxonomy():
  """Taxonomy data page"""
  try:
    # TODO: Implement taxonomy listing logic
    return render_template('taxonomy.html')
  except Exception as e:
    current_app.logger.error(f"Taxonomy page error: {e}")
    flash(f"Error loading taxonomy: {str(e)}", 'error')
    return redirect(url_for('main.dashboard'))


@main_bp.route('/analysis')
@login_required
def analysis():
  """Analysis page"""
  try:
    # TODO: Implement analysis logic
    return render_template('analysis.html')
  except Exception as e:
    current_app.logger.error(f"Analysis page error: {e}")
    flash(f"Error loading analysis: {str(e)}", 'error')
    return redirect(url_for('main.dashboard'))


@main_bp.route('/data-upload')
@login_required
def data_upload():
  """Data upload page"""
  try:
    # TODO: Implement data upload logic
    return render_template('data_upload.html')
  except Exception as e:
    current_app.logger.error(f"Data upload page error: {e}")
    flash(f"Error loading data upload: {str(e)}", 'error')
    return redirect(url_for('main.dashboard'))


@main_bp.route('/reports')
@login_required
def reports():
  """Reports page"""
  try:
    # TODO: Implement reports logic
    return render_template('reports.html')
  except Exception as e:
    current_app.logger.error(f"Reports page error: {e}")
    flash(f"Error loading reports: {str(e)}", 'error')
    return redirect(url_for('main.dashboard'))


@main_bp.route('/settings')
@login_required
def settings():
  """User settings page"""
  try:
    # TODO: Implement settings logic
    return render_template('settings.html')
  except Exception as e:
    current_app.logger.error(f"Settings page error: {e}")
    flash(f"Error loading settings: {str(e)}", 'error')
    return redirect(url_for('main.dashboard'))


@main_bp.route('/patients/new')
@login_required
def new_patient():
  """New patient form page"""
  try:
    # TODO: Implement new patient form
    flash("New patient form coming soon!", 'info')
    return redirect(url_for('main.patients'))
  except Exception as e:
    current_app.logger.error(f"New patient page error: {e}")
    flash(f"Error loading new patient form: {str(e)}", 'error')
    return redirect(url_for('main.patients'))


@main_bp.route('/analysis/new')
@login_required
def new_analysis():
  """New analysis form page"""
  try:
    # TODO: Implement new analysis form
    flash("New analysis form coming soon!", 'info')
    return redirect(url_for('main.analysis'))
  except Exception as e:
    current_app.logger.error(f"New analysis page error: {e}")
    flash(f"Error loading new analysis form: {str(e)}", 'error')
    return redirect(url_for('main.analysis'))
