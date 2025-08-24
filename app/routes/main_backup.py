"""
Main web routes for MVA2 application

Handles the main web interface routes for the application.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from .. import db

main_bp = Blueprint('main', __name__)

def _get_models():
    """Helper function to import models lazily"""
    from ..models import Patient, Analysis, Taxonomy
    return Patient, Analysis, Taxonomy


@main_bp.route('/')
def index():
  """Landing page"""
  if current_user.is_authenticated:
    return redirect(url_for('main.dashboard'))
  return render_template('index.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
  """Main dashboard"""
  try:
    # Import models locally to avoid circular imports
    Patient, Analysis, Taxonomy = _get_models()
    
    # Get summary statistics
    patient_count = Patient.query.filter_by(user_id=current_user.id).count()
    analysis_count = Analysis.query.filter_by(user_id=current_user.id).count()
    taxonomy_count = Taxonomy.query.filter_by(user_id=current_user.id).count()

    # Get recent analyses
    recent_analyses = Analysis.query.filter_by(user_id=current_user.id)\
        .order_by(Analysis.created_at.desc()).limit(5).all()

    return render_template('dashboard.html',
                           patient_count=patient_count,
                           analysis_count=analysis_count,
                           taxonomy_count=taxonomy_count,
                           recent_analyses=recent_analyses)
  except Exception as e:
    current_app.logger.error(f"Dashboard error: {e}")
    flash('Error loading dashboard', 'error')
    return render_template('dashboard.html',
                           patient_count=0,
                           analysis_count=0,
                           taxonomy_count=0,
                           recent_analyses=[])


@main_bp.route('/patients')
@login_required
def patients():
  """Patient management page"""
  return render_template('patients/index.html')


@main_bp.route('/patients/new')
@login_required
def new_patient():
  """New patient form"""
  return render_template('patients/new.html')


@main_bp.route('/patients/<int:patient_id>')
@login_required
def patient_detail(patient_id):
  """Patient detail page"""
  patient = Patient.query.filter_by(
      id=patient_id, user_id=current_user.id).first_or_404()
  return render_template('patients/detail.html', patient=patient)


@main_bp.route('/patients/<int:patient_id>/edit')
@login_required
def edit_patient(patient_id):
  """Edit patient form"""
  patient = Patient.query.filter_by(
      id=patient_id, user_id=current_user.id).first_or_404()
  return render_template('patients/edit.html', patient=patient)


@main_bp.route('/taxonomy')
@login_required
def taxonomy():
  """Taxonomy management page"""
  return render_template('taxonomy/index.html')


@main_bp.route('/taxonomy/<int:taxonomy_id>')
@login_required
def taxonomy_detail(taxonomy_id):
  """Taxonomy detail page"""
  taxonomy = Taxonomy.query.filter_by(
      id=taxonomy_id, user_id=current_user.id).first_or_404()
  return render_template('taxonomy/detail.html', taxonomy=taxonomy)


@main_bp.route('/analysis')
@login_required
def analysis():
  """Analysis management page"""
  return render_template('analysis/index.html')


@main_bp.route('/analysis/new')
@login_required
def new_analysis():
  """New analysis form"""
  return render_template('analysis/new.html')


@main_bp.route('/analysis/<int:analysis_id>')
@login_required
def analysis_detail(analysis_id):
  """Analysis detail page"""
  analysis = Analysis.query.filter_by(
      id=analysis_id, user_id=current_user.id).first_or_404()
  return render_template('analysis/detail.html', analysis=analysis)


@main_bp.route('/analysis/<int:analysis_id>/results')
@login_required
def analysis_results(analysis_id):
  """Analysis results page"""
  analysis = Analysis.query.filter_by(
      id=analysis_id, user_id=current_user.id).first_or_404()
  return render_template('analysis/results.html', analysis=analysis)


@main_bp.route('/data-upload')
@login_required
def data_upload():
  """Data upload page"""
  return render_template('data/upload.html')


@main_bp.route('/reports')
@login_required
def reports():
  """Reports and exports page"""
  return render_template('reports/index.html')


@main_bp.route('/settings')
@login_required
def settings():
  """User settings page"""
  return render_template('settings/index.html')


@main_bp.route('/help')
def help():
  """Help and documentation page"""
  return render_template('help/index.html')


@main_bp.route('/about')
def about():
  """About page"""
  return render_template('about.html')


@main_bp.route('/privacy')
def privacy():
  """Privacy policy page"""
  return render_template('privacy.html')


@main_bp.route('/terms')
def terms():
  """Terms of service page"""
  return render_template('terms.html')

# Error handlers


@main_bp.errorhandler(404)
def not_found_error(error):
  """Handle 404 errors"""
  return render_template('errors/404.html'), 404


@main_bp.errorhandler(500)
def internal_error(error):
  """Handle 500 errors"""
  db.session.rollback()
  return render_template('errors/500.html'), 500


@main_bp.errorhandler(403)
def forbidden_error(error):
  """Handle 403 errors"""
  return render_template('errors/403.html'), 403

# API-like endpoints for AJAX requests


@main_bp.route('/api/quick-stats')
@login_required
def quick_stats():
  """Quick statistics for dashboard widgets"""
  try:
    stats = {
        'patients': Patient.query.filter_by(user_id=current_user.id).count(),
        'analyses': Analysis.query.filter_by(user_id=current_user.id).count(),
        'taxonomies': Taxonomy.query.filter_by(user_id=current_user.id).count(),
        'recent_activity': []
    }

    # Get recent activity
    recent_analyses = Analysis.query.filter_by(user_id=current_user.id)\
        .order_by(Analysis.updated_at.desc()).limit(3).all()

    for analysis in recent_analyses:
      stats['recent_activity'].append({
          'type': 'analysis',
          'name': analysis.name,
          'status': analysis.status.value if analysis.status else 'unknown',
          'updated_at': analysis.updated_at.isoformat() if analysis.updated_at else None
      })

    return jsonify(stats)

  except Exception as e:
    current_app.logger.error(f"Quick stats error: {e}")
    return jsonify({'error': 'Failed to load statistics'}), 500


@main_bp.route('/api/search')
@login_required
def search():
  """Global search across patients, analyses, and taxonomies"""
  try:
    query = request.args.get('q', '').strip()
    if not query:
      return jsonify({'results': []})

    results = []

    # Search patients
    patients = Patient.query.filter_by(user_id=current_user.id)\
        .filter(Patient.patient_id.ilike(f'%{query}%')).limit(5).all()

    for patient in patients:
      results.append({
          'type': 'patient',
          'id': patient.id,
          'title': patient.patient_id,
          'subtitle': f"Age: {patient.age}, Sex: {patient.sex}" if patient.age and patient.sex else "",
          'url': url_for('main.patient_detail', patient_id=patient.id)
      })

    # Search analyses
    analyses = Analysis.query.filter_by(user_id=current_user.id)\
        .filter(Analysis.name.ilike(f'%{query}%')).limit(5).all()

    for analysis in analyses:
      results.append({
          'type': 'analysis',
          'id': analysis.id,
          'title': analysis.name,
          'subtitle': f"Type: {analysis.analysis_type.value}" if analysis.analysis_type else "",
          'url': url_for('main.analysis_detail', analysis_id=analysis.id)
      })

    # Search taxonomies
    taxonomies = Taxonomy.query.filter_by(user_id=current_user.id)\
        .filter(Taxonomy.taxonomy_id.ilike(f'%{query}%')).limit(5).all()

    for taxonomy in taxonomies:
      results.append({
          'type': 'taxonomy',
          'id': taxonomy.id,
          'title': taxonomy.taxonomy_id,
          'subtitle': taxonomy.get_display_name(),
          'url': url_for('main.taxonomy_detail', taxonomy_id=taxonomy.id)
      })

    return jsonify({'results': results})

  except Exception as e:
    current_app.logger.error(f"Search error: {e}")
    return jsonify({'error': 'Search failed'}), 500
