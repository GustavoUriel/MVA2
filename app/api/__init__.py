"""
API blueprint for MVA2 application

Provides RESTful API endpoints for data analysis and visualization.
"""

from flask import Blueprint
from flask_restx import Api

# Create API blueprint
bp = Blueprint('api', __name__)

# Initialize Flask-RESTX API
api = Api(
    bp,
    title='MVA2 API',
    version='1.0',
    description='Multiple Myeloma Multivariate Analysis API',
    doc='/docs/'
)

# Import and register namespaces when available
# TODO: Add namespaces as they are implemented
