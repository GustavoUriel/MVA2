"""
Analysis blueprint for MVA2 application
"""

from flask import Blueprint

bp = Blueprint('analysis', __name__)

from . import routes
