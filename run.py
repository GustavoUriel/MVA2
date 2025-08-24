"""
Main Flask application entry point for MVA2 - Multiple Myeloma Analysis Application
Author: MVA2 Development Team
Date: 2025
"""

from app import create_app, db
from app.models.user import User
from app.models.patient import Patient
from app.models.taxonomy import Taxonomy
from app.models.analysis import Analysis

# Create Flask application instance
app = create_app()


@app.shell_context_processor
def make_shell_context():
  """Make database models available in Flask shell context"""
  return {
      'db': db,
      'User': User,
      'Patient': Patient,
      'Taxonomy': Taxonomy,
      'Analysis': Analysis
  }


@app.cli.command()
def init_db():
  """Initialize the database with tables"""
  db.create_all()
  print("Database initialized successfully!")


@app.cli.command()
def create_admin():
  """Create an admin user"""
  from app.models.user import User
  from werkzeug.security import generate_password_hash

  admin = User(
      email='admin@mva2.com',
      username='admin',
      first_name='Admin',
      last_name='User',
      role='admin',
      is_active=True
  )
  admin.password_hash = generate_password_hash('admin123')

  db.session.add(admin)
  db.session.commit()
  print("Admin user created successfully!")


if __name__ == '__main__':
  app.run(debug=True, host='0.0.0.0', port=5000)
