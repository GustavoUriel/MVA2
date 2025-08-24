#!/usr/bin/env python3
"""
Database initialization script for MVA2
Creates all database tables and initializes the database schema.
"""

from app.models.analysis import Analysis, SavedView
from app.models.taxonomy import Taxonomy, BrackenResult
from app.models.patient import Patient
from app.models.user import User
from app import create_app, db
import os
import sys
from dotenv import load_dotenv

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Load environment variables
load_dotenv()

# Import Flask app and database

# Import all models to ensure they are registered with SQLAlchemy


def init_database():
  """Initialize the database with all tables"""
  app = create_app()

  with app.app_context():
    print("Creating database tables...")

    # Drop all tables (for fresh start)
    db.drop_all()

    # Create all tables
    db.create_all()

    print("Database initialization completed successfully!")

    # Verify tables were created
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"Created tables: {sorted(tables)}")

    return True


if __name__ == '__main__':
  try:
    init_database()
    print("\n✅ Database initialization successful!")
  except Exception as e:
    print(f"\n❌ Database initialization failed: {e}")
    sys.exit(1)
