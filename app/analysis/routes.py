"""
Analysis routes for MVA2 application
"""

from flask import render_template, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from . import bp


@bp.route('/dashboard')
@login_required
def dashboard():
  """Analysis dashboard"""
  return render_template('analysis/dashboard.html')


@bp.route('/new')
@login_required
def new():
  """Create new analysis"""
  return render_template('analysis/new.html')


@bp.route('/view/<int:analysis_id>')
@login_required
def view(analysis_id):
  """View analysis results"""
  return render_template('analysis/view.html', analysis_id=analysis_id)
