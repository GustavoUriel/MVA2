"""
Analysis routes for MVA2 application
"""

from flask import render_template, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from . import bp
from ..utils.logging_utils import log_function, log_analysis_event, user_logger


@bp.route('/dashboard')
@login_required
@log_function('main')
def dashboard():
  """Analysis dashboard"""
  log_analysis_event('general', 'Dashboard accessed', user=current_user.email)
  return render_template('analysis/dashboard.html')


@bp.route('/new')
@login_required
@log_function('main')
def new():
  """Create new analysis"""
  log_analysis_event('general', 'New analysis page accessed', user=current_user.email)
  return render_template('analysis/new.html')


@bp.route('/view/<int:analysis_id>')
@login_required
@log_function('main')
def view(analysis_id):
  """View analysis results"""
  log_analysis_event('general', 'Analysis results viewed', 
                    analysis_id=analysis_id, user=current_user.email)
  return render_template('analysis/view.html', analysis_id=analysis_id)
