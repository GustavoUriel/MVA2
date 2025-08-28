"""
Main web routes for MVA2 application

Handles the main web interface routes for the application.
"""

from ..models.taxonomy import Taxonomy
from app.utils.logging_utils import log_function, user_logger
import traceback
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, make_response
from flask_login import login_required, current_user
from .. import db
from ..utils.logging_utils import log_function, user_logger

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@log_function('main')
def index():
  """Home page"""
  # Force check authentication status
  if current_user.is_authenticated:
    current_app.logger.info(
        f"Authenticated user {current_user.email} accessing index, redirecting to dashboard")
    return redirect(url_for('main.dashboard'))

  current_app.logger.info(
      "Unauthenticated user accessing index, showing welcome page")
  # Return welcome page with cache control headers to prevent caching
  response = make_response(render_template('index.html'))
  response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
  response.headers['Pragma'] = 'no-cache'
  response.headers['Expires'] = '0'
  return response


@main_bp.route('/dashboard')
@login_required
@log_function('main')
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
    traceback.print_exc()  # This prints the full traceback
    current_app.logger.error(f"Dashboard error: {e}")
    flash(f"Error loading dashboard: {str(e)}", 'error')
    return redirect(url_for('main.index'))


@main_bp.route('/about')
@log_function('main')
def about():
  """About page"""
  return render_template('about.html')


@main_bp.route('/contact')
@log_function('main')
def contact():
  """Contact page"""
  return render_template('contact.html')


@main_bp.route('/health')
@log_function('main')
def health():
  """Health check endpoint"""
  return jsonify({'status': 'healthy', 'message': 'MVA2 is running'})


@main_bp.route('/patients')
@login_required
@log_function('main')
def patients():
  """Patients management page"""
  try:
    # TODO: Implement patient listing logic
    return render_template('patients.html')
  except Exception as e:
    traceback.print_exc()  # This prints the full traceback
    current_app.logger.error(f"Patients page error: {e}")
    flash(f"Error loading patients: {str(e)}", 'error')
    return redirect(url_for('main.dashboard'))


@main_bp.route('/taxonomy')
@login_required
@log_function('main')
def taxonomy():
  """Taxonomy data page"""
  try:
    # Provide an initial page of taxonomy data so the table isn't empty on first load
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)

    try:
      pagination = Taxonomy.query.filter_by(user_id=current_user.id).paginate(
          page=page, per_page=per_page, error_out=False)
      taxonomies = [t.to_dict() for t in pagination.items]
      initial_meta = {
          'total_count': pagination.total,
          'page': page,
          'per_page': per_page,
          'pages': pagination.pages
      }
    except Exception:
      taxonomies = []
      initial_meta = {'total_count': 0, 'page': 1,
                      'per_page': per_page, 'pages': 0}

    return render_template('taxonomy.html', initial_taxonomies=taxonomies, initial_meta=initial_meta)
  except Exception as e:
    traceback.print_exc()  # This prints the full traceback
    current_app.logger.error(f"Taxonomy page error: {e}")
    flash(f"Error loading taxonomy: {str(e)}", 'error')
    return redirect(url_for('main.dashboard'))


@main_bp.route('/analysis')
@login_required
@log_function('main')
def analysis():
  """Analysis page"""
  try:
    # TODO: Implement analysis logic
    return render_template('analysis.html')
  except Exception as e:
    traceback.print_exc()  # This prints the full traceback
    current_app.logger.error(f"Analysis page error: {e}")
    flash(f"Error loading analysis: {str(e)}", 'error')
    return redirect(url_for('main.dashboard'))


@main_bp.route('/data-upload')
@login_required
@log_function('user_events')
def data_upload():
  """Data upload page"""
  try:
    user_logger.log_user_event(
        'Data upload page accessed', user=current_user.email, ip=request.remote_addr)
    return render_template('data_upload.html')
  except Exception as e:
    user_logger.log_error('user_events', e, 'Data upload page access')
    flash(f"Error loading data upload: {str(e)}", 'error')
    return redirect(url_for('main.dashboard'))


@main_bp.route('/reports')
@login_required
@log_function('main')
def reports():
  """Reports page"""
  try:
    # TODO: Implement reports logic
    return render_template('reports.html')
  except Exception as e:
    traceback.print_exc()  # This prints the full traceback
    current_app.logger.error(f"Reports page error: {e}")
    flash(f"Error loading reports: {str(e)}", 'error')
    return redirect(url_for('main.dashboard'))


@main_bp.route('/settings')
@login_required
@log_function('main')
def settings():
  """User settings page"""
  try:
    # TODO: Implement settings logic
    return render_template('settings.html')
  except Exception as e:
    traceback.print_exc()  # This prints the full traceback
    current_app.logger.error(f"Settings page error: {e}")
    flash(f"Error loading settings: {str(e)}", 'error')
    return redirect(url_for('main.dashboard'))


@main_bp.route('/patients/new')
@login_required
@log_function('main')
def new_patient():
  """New patient form page"""
  try:
    # TODO: Implement new patient form
    flash("New patient form coming soon!", 'info')
    return redirect(url_for('main.patients'))
  except Exception as e:
    traceback.print_exc()  # This prints the full traceback
    current_app.logger.error(f"New patient page error: {e}")
    flash(f"Error loading new patient form: {str(e)}", 'error')
    return redirect(url_for('main.patients'))


@main_bp.route('/analysis/new')
@login_required
@log_function('main')
def new_analysis():
  """New analysis form page"""
  try:
    # TODO: Implement new analysis form
    flash("New analysis form coming soon!", 'info')
    return redirect(url_for('main.analysis'))
  except Exception as e:
    traceback.print_exc()  # This prints the full traceback
    current_app.logger.error(f"New analysis page error: {e}")
    flash(f"Error loading new analysis form: {str(e)}", 'error')
    return redirect(url_for('main.analysis'))


@main_bp.route('/api/quick-stats')
@login_required
@log_function('main')
def quick_stats():
  """Quick statistics for dashboard widgets"""
  try:
    # TODO: Replace with actual database queries when models are fully implemented
    stats = {
        # Patient.query.filter_by(user_id=current_user.id).count(),
        'patients': 0,
        # Analysis.query.filter_by(user_id=current_user.id).count(),
        'analyses': 0,
        # Taxonomy.query.filter_by(user_id=current_user.id).count(),
        'taxonomies': 0,
        'recent_activity': [
            {
                'type': 'analysis',
                'name': 'Sample Analysis',
                'status': 'completed',
                'updated_at': '2025-08-24T19:00:00Z'
            }
        ]
    }

    return jsonify(stats)

  except Exception as e:
    traceback.print_exc()  # This prints the full traceback
    current_app.logger.error(f"Quick stats error: {e}")
    return jsonify({'error': 'Failed to load statistics'}), 500
