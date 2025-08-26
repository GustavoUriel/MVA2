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

# Import and register namespaces
try:
  from .auth import auth_ns
  api.add_namespace(auth_ns, path='/auth')
except Exception as e:
  import traceback
  traceback.print_exc()  # This prints the full traceback
  # Defer errors to runtime logs
  pass

try:
  from .patients import patients_ns
  api.add_namespace(patients_ns, path='/patients')
except Exception as e:
  import traceback
  traceback.print_exc()
  pass

try:
  from .uploads import uploads_ns
  api.add_namespace(uploads_ns, path='/uploads')
except Exception as e:
  import traceback
  traceback.print_exc()
  pass

try:
  from .logs import logs_ns
  api.add_namespace(logs_ns, path='/logs')
except Exception:
  pass

try:
  from .admin_logs import admin_ns
  api.add_namespace(admin_ns, path='/admin')
except Exception:
  pass
