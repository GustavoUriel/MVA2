"""
Flask Application Factory for MVA2 - Multiple Myeloma Analysis Application

This module creates and configures the Flask application with all necessary
extensions, blueprints, and configurations for a production-ready biomedical
research platform.

Features:
- Google OAuth2.0 authentication
- Role-based access control
- Database models for patients, taxonomies, and analyses
- Advanced statistical analysis capabilities
- Microbiome data processing
- Publication-ready report generation
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, current_app, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from flask_caching import Cache
from authlib.integrations.flask_client import OAuth
from config import Config, DevelopmentConfig, ProductionConfig, TestingConfig
import redis
from flask_moment import Moment


# Initialize Flask extensions
moment = Moment()
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"  # Use memory for now, Redis for production
)
cache = Cache(config={'CACHE_TYPE': 'simple'})  # Simple cache for development
oauth = OAuth()


def create_app(config_class=None):
  """
  Application factory pattern for creating Flask app instances

  Args:
      config_class: Configuration class to use (defaults to environment-based)

  Returns:
      Flask application instance
  """
  flask_app = Flask(__name__)

  # Load configuration based on environment
  if config_class is None:
    env = os.environ.get('FLASK_ENV', 'development')
    if env == 'production':
      config_class = ProductionConfig
    elif env == 'testing':
      config_class = TestingConfig
    else:
      config_class = DevelopmentConfig

  flask_app.config.from_object(config_class)

  # Initialize Flask extensions with app
  db.init_app(flask_app)
  migrate.init_app(flask_app, db)
  login_manager.init_app(flask_app)
  csrf.init_app(flask_app)
  limiter.init_app(flask_app)
  cache.init_app(flask_app)
  oauth.init_app(flask_app)

  # Configure CORS for API endpoints
  CORS(flask_app, resources={
      r"/api/*": {"origins": "*"},
      r"/auth/*": {"origins": "*"}
  })

  # Configure login manager
  login_manager.login_view = 'auth.login'
  login_manager.login_message = 'Please log in to access this page.'
  login_manager.login_message_category = 'info'

  @login_manager.user_loader
  def load_user(user_id):
    from .models.user import User
    return User.query.get(int(user_id))

  # Configure Google OAuth
  google = oauth.register(
      name='google',
      client_id=flask_app.config.get('GOOGLE_CLIENT_ID'),
      client_secret=flask_app.config.get('GOOGLE_CLIENT_SECRET'),
      server_metadata_url='https://accounts.google.com/.well-known/openid_configuration',
      client_kwargs={
          'scope': 'openid email profile'
      }
  )

  # Register blueprints
  from app.routes.main import main_bp
  flask_app.register_blueprint(main_bp)

  from app.auth import bp as auth_bp
  flask_app.register_blueprint(auth_bp, url_prefix='/auth')

  from app.api import bp as api_bp
  flask_app.register_blueprint(api_bp, url_prefix='/api/v1')

  from app.data import bp as data_bp
  flask_app.register_blueprint(data_bp, url_prefix='/data')

  from app.analysis import bp as analysis_bp
  flask_app.register_blueprint(analysis_bp, url_prefix='/analysis')

  # Models will be imported when needed to avoid circular imports
  # Each route/module should import models individually:
  # from .models.user import User

  # Configure logging
  if not flask_app.debug and not flask_app.testing:
    configure_logging(flask_app)

  # Create user instance directories using modern Flask pattern
  @flask_app.before_request
  def create_instance_directories():
    """Create instance directories for user data storage"""
    if not hasattr(create_instance_directories, 'executed'):
      instance_path = os.path.join(flask_app.instance_path, 'users')
      os.makedirs(instance_path, exist_ok=True)
      create_instance_directories.executed = True

  # Add template global functions
  @flask_app.template_global()
  def get_user_folder(email):
    """Get user-specific folder path"""
    safe_email = email.replace('@', '_').replace('.', '_')
    return os.path.join(flask_app.instance_path, 'users', safe_email)

  # Error handlers
  @flask_app.errorhandler(404)
  def not_found_error(error):
    return render_template('errors/404.html'), 404

  @flask_app.errorhandler(500)
  def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

  @flask_app.errorhandler(403)
  def forbidden_error(error):
    return render_template('errors/403.html'), 403

  # Security headers
  @flask_app.after_request
  def security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

    # Content Security Policy
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "img-src 'self' data: https:; "
        "font-src 'self' https://cdn.jsdelivr.net; "
        "connect-src 'self' https://accounts.google.com; "
        "frame-src 'none';"
    )
    response.headers['Content-Security-Policy'] = csp

    return response

  return flask_app


def configure_logging(app):
  """
  Configure application logging for production

  Args:
      app: Flask application instance
  """
  if not os.path.exists('logs'):
    os.mkdir('logs')

  file_handler = RotatingFileHandler(
      'logs/mva2.log',
      maxBytes=10240000,
      backupCount=10
  )

  file_handler.setFormatter(logging.Formatter(
      '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
  ))

  file_handler.setLevel(logging.INFO)
  app.logger.addHandler(file_handler)
  app.logger.setLevel(logging.INFO)
  app.logger.info('MVA2 application startup')


# Import models to ensure they are registered with SQLAlchemy
