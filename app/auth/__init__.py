"""
Authentication blueprint for MVA2 application
"""

from flask import Blueprint

bp = Blueprint('auth', __name__)

from . import routes
