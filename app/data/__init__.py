"""
Data management blueprint for MVA2 application
"""

from flask import Blueprint

bp = Blueprint('data', __name__)

from . import routes
