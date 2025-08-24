"""
Data management routes for MVA2 application
"""

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from . import bp


@bp.route('/upload')
@login_required
def upload():
  """Data upload page"""
  return render_template('data/upload.html')


@bp.route('/manage')
@login_required
def manage():
  """Data management page"""
  return render_template('data/manage.html')
