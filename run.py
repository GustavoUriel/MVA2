"""
Main Flask application entry point for MVA2 - Multiple Myeloma Analysis Application
Author: MVA2 Development Team
Date: 2025
"""

from app.models.analysis import Analysis
from app.models.taxonomy import Taxonomy
from app.models.patient import Patient
from app.models.user import User
from app import create_app, db
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


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
  import getpass
  from app.models.user import User
  from werkzeug.security import generate_password_hash

  # Get admin credentials interactively
  print("Creating admin user...")
  email = input("Enter admin email: ").strip()
  if not email:
    print("Email is required!")
    return
  
  username = input("Enter admin username (or press Enter for default): ").strip()
  if not username:
    username = 'admin'
  
  # Check if admin already exists
  existing_admin = User.query.filter_by(email=email).first()
  if existing_admin:
    print(f"User with email {email} already exists!")
    return
  
  # Get password securely
  password = getpass.getpass("Enter admin password: ")
  if not password:
    print("Password is required!")
    return
  
  password_confirm = getpass.getpass("Confirm admin password: ")
  if password != password_confirm:
    print("Passwords do not match!")
    return
  
  if len(password) < 8:
    print("Password must be at least 8 characters long!")
    return

  admin = User(
      email=email,
      username=username,
      first_name='Admin',
      last_name='User',
      role='admin',
      is_active=True
  )
  admin.password_hash = generate_password_hash(password)

  db.session.add(admin)
  db.session.commit()
  print(f"Admin user {email} created successfully!")


if __name__ == '__main__':
  app.run(debug=True, host='0.0.0.0', port=5000)
