"""
User model for MVA2 application

Handles user authentication, authorization, and profile management
with support for Google OAuth, role-based access control, and audit trails.
"""

from datetime import datetime, timedelta
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .. import db
import json
import os


class User(UserMixin, db.Model):
  """
  User model with comprehensive authentication and authorization features

  Features:
  - Google OAuth integration
  - Role-based access control (Admin, Researcher, Analyst, Viewer)
  - Session management and security
  - User activity tracking
  - Personal data storage management
  """

  __tablename__ = 'users'

  # Primary identification
  id = db.Column(db.Integer, primary_key=True)
  email = db.Column(db.String(120), unique=True, nullable=False, index=True)
  username = db.Column(db.String(80), unique=True, nullable=True)

  # Profile information
  first_name = db.Column(db.String(50), nullable=True)
  last_name = db.Column(db.String(50), nullable=True)
  profile_picture_url = db.Column(db.String(255), nullable=True)
  institution = db.Column(db.String(100), nullable=True)
  department = db.Column(db.String(100), nullable=True)

  # Authentication
  password_hash = db.Column(db.String(255), nullable=True)
  google_id = db.Column(db.String(100), unique=True, nullable=True)
  is_active = db.Column(db.Boolean, default=True, nullable=False)
  is_verified = db.Column(db.Boolean, default=False, nullable=False)

  # Authorization and roles
  role = db.Column(db.String(20), default='viewer', nullable=False)
  permissions = db.Column(db.Text, nullable=True)  # JSON string

  # Security and session management
  failed_login_attempts = db.Column(db.Integer, default=0)
  account_locked_until = db.Column(db.DateTime, nullable=True)
  last_login = db.Column(db.DateTime, nullable=True)
  last_activity = db.Column(db.DateTime, default=datetime.utcnow)
  session_timeout = db.Column(db.Integer, default=1440)  # minutes

  # Account metadata
  created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
  updated_at = db.Column(
      db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  # User preferences and settings
  preferences = db.Column(db.Text, nullable=True)  # JSON string
  timezone = db.Column(db.String(50), default='UTC')
  language = db.Column(db.String(10), default='en')

  # Data storage tracking
  saved_views = db.Column(db.Text, nullable=True)  # JSON string
  saved_datasets = db.Column(db.Text, nullable=True)  # JSON string
  saved_results = db.Column(db.Text, nullable=True)  # JSON string

  # Usage tracking
  total_analyses = db.Column(db.Integer, default=0)
  last_analysis_date = db.Column(db.DateTime, nullable=True)
  storage_used_mb = db.Column(db.Float, default=0.0)

  # Relationships
  analyses = db.relationship('Analysis', backref='user', lazy='dynamic',
                             cascade='all, delete-orphan')
  patients = db.relationship('Patient', backref='owner', lazy='dynamic',
                             cascade='all, delete-orphan')

  def __repr__(self):
    return f'<User {self.email}>'

  def set_password(self, password):
    """Set password hash for the user"""
    self.password_hash = generate_password_hash(password)

  def check_password(self, password):
    """Check if provided password matches the hash"""
    if not self.password_hash:
      return False
    return check_password_hash(self.password_hash, password)

  def record_login_attempt(self, success=True):
    """Record login attempt and handle account locking"""
    if success:
      self.failed_login_attempts = 0
      self.account_locked_until = None
      self.last_login = datetime.utcnow()
    else:
      self.failed_login_attempts += 1
      if self.failed_login_attempts >= 5:
        # Lock account for 30 minutes
        self.account_locked_until = datetime.utcnow() + timedelta(minutes=30)

    self.last_activity = datetime.utcnow()
    db.session.commit()

  def is_account_locked(self):
    """Check if account is currently locked"""
    if not self.account_locked_until:
      return False
    return datetime.utcnow() < self.account_locked_until

  def has_permission(self, permission):
    """Check if user has specific permission"""
    if self.role == 'admin':
      return True

    if not self.permissions:
      return False

    perms = json.loads(self.permissions)
    return permission in perms

  def get_role_permissions(self):
    """Get permissions based on user role"""
    from config import USER_ROLES
    return USER_ROLES.get(self.role, {}).get('permissions', [])

  def update_activity(self):
    """Update last activity timestamp"""
    self.last_activity = datetime.utcnow()
    db.session.commit()

  def get_user_folder(self):
    """Get user-specific folder path for data storage"""
    safe_email = self.email.replace('@', '_').replace('.', '_')
    folder_path = os.path.join(current_app.instance_path, 'users', safe_email)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

  def get_saved_views(self):
    """Get list of saved views"""
    if not self.saved_views:
      return []
    return json.loads(self.saved_views)

  def add_saved_view(self, name, parameters, description=None):
    """Add a new saved view"""
    views = self.get_saved_views()
    view_data = {
        'name': name,
        'parameters': parameters,
        'description': description,
        'created_at': datetime.utcnow().isoformat(),
        'file_path': os.path.join(self.get_user_folder(), f'view_{name}.json')
    }

    # Save parameters to file
    with open(view_data['file_path'], 'w') as f:
      json.dump(parameters, f, indent=2)

    views.append(view_data)
    self.saved_views = json.dumps(views)
    db.session.commit()

  def delete_saved_view(self, name):
    """Delete a saved view"""
    views = self.get_saved_views()
    views = [v for v in views if v['name'] != name]
    self.saved_views = json.dumps(views)

    # Delete file
    view_file = os.path.join(self.get_user_folder(), f'view_{name}.json')
    if os.path.exists(view_file):
      os.remove(view_file)

    db.session.commit()

  def get_saved_results(self):
    """Get list of saved results"""
    if not self.saved_results:
      return []
    return json.loads(self.saved_results)

  def add_saved_result(self, name, file_path, result_type='analysis'):
    """Add a new saved result"""
    results = self.get_saved_results()
    result_data = {
        'name': name,
        'file_path': file_path,
        'type': result_type,
        'created_at': datetime.utcnow().isoformat(),
        'size_mb': os.path.getsize(file_path) / (1024 * 1024) if os.path.exists(file_path) else 0
    }

    results.append(result_data)
    self.saved_results = json.dumps(results)
    self.update_storage_usage()
    db.session.commit()

  def share_result_with_user(self, result_name, target_user_email):
    """Share a result with another user"""
    target_user = User.query.filter_by(email=target_user_email).first()
    if not target_user:
      return False

    # Find the result
    results = self.get_saved_results()
    result = next((r for r in results if r['name'] == result_name), None)
    if not result:
      return False

    # Copy result to target user with attribution
    shared_name = f"{result_name} (from {self.email})"
    target_results = target_user.get_saved_results()

    # Copy file to target user's folder
    source_path = result['file_path']
    target_folder = target_user.get_user_folder()
    target_path = os.path.join(target_folder, os.path.basename(source_path))

    if os.path.exists(source_path):
      import shutil
      shutil.copy2(source_path, target_path)

    target_user.add_saved_result(shared_name, target_path, result['type'])
    return True

  def update_storage_usage(self):
    """Update storage usage calculation"""
    total_size = 0
    user_folder = self.get_user_folder()

    for root, dirs, files in os.walk(user_folder):
      for file in files:
        file_path = os.path.join(root, file)
        if os.path.exists(file_path):
          total_size += os.path.getsize(file_path)

    self.storage_used_mb = total_size / (1024 * 1024)
    db.session.commit()

  def cleanup_unused_files(self):
    """Clean up files not referenced by any user"""
    # This would be called periodically to clean up orphaned files
    pass

  def to_dict(self):
    """Convert user to dictionary for API responses"""
    return {
        'id': self.id,
        'email': self.email,
        'username': self.username,
        'first_name': self.first_name,
        'last_name': self.last_name,
        'role': self.role,
        'is_active': self.is_active,
        'is_verified': self.is_verified,
        'created_at': self.created_at.isoformat() if self.created_at else None,
        'last_login': self.last_login.isoformat() if self.last_login else None,
        'total_analyses': self.total_analyses,
        'storage_used_mb': self.storage_used_mb
    }

  @staticmethod
  def create_from_google(google_user_info):
    """Create user from Google OAuth information"""
    user = User(
        email=google_user_info.get('email'),
        google_id=google_user_info.get('sub'),
        first_name=google_user_info.get('given_name'),
        last_name=google_user_info.get('family_name'),
        profile_picture_url=google_user_info.get('picture'),
        is_verified=google_user_info.get('email_verified', False),
        role='viewer'  # Default role for new users
    )

    # Generate username from email
    username_base = user.email.split('@')[0]
    counter = 1
    username = username_base
    while User.query.filter_by(username=username).first():
      username = f"{username_base}{counter}"
      counter += 1
    user.username = username

    db.session.add(user)
    db.session.commit()
    return user
