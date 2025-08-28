#!/usr/bin/env python3
"""
Test the actual Bracken import process
"""

from config import BRACKEN_TIME_POINTS
import pandas as pd
from flask_login import login_user
from app.models.taxonomy import BrackenResult
from app.models.user import User
from app import create_app, db
import sys
import os
sys.path.insert(0, os.path.abspath('.'))


def test_bracken_import():
  """Test the actual Bracken import process"""

  print("=== Testing Bracken Import Process ===")

  app = create_app()

  with app.app_context():
    # Get or create a test user
    user = User.query.filter_by(email='test@example.com').first()
    if not user:
      user = User(
          username='testuser',
          email='test@example.com',
          first_name='Test',
          last_name='User'
      )
      user.set_password('testpass')
      db.session.add(user)
      db.session.commit()

    print(f"Using user: {user.email}")

    # Clear existing Bracken results for this user
    existing = BrackenResult.query.filter_by(user_id=user.id).count()
    if existing > 0:
      BrackenResult.query.filter_by(user_id=user.id).delete()
      db.session.commit()
      print(f"Cleared {existing} existing BrackenResult records")

    # Load CSV data
    df = pd.read_csv('instance/bracken.csv', sep=';')
    print(f"Loaded CSV with {len(df)} rows")

    # Process a few rows manually using the same logic as the upload function
    records_added = 0
    rows_processed = 0

    for idx, row in df.head(100).iterrows():  # Test first 100 rows
      rows_processed += 1

      # Get taxonomy ID from first column
      taxonomy_id = str(row.iloc[0]).strip()
      if pd.isna(taxonomy_id) or taxonomy_id == '':
        continue

      row_has_data = False

      # Process each data column
      for col in df.columns[1:]:  # Skip taxonomy column
        col_stripped = col.strip()

        # Check if this column has data
        if pd.isna(row[col]) or str(row[col]).strip() in ['-', '']:
          continue

        # Check if this is a valid timepoint column
        patient_id = None
        timepoint = None

        for tp_key, tp_config in BRACKEN_TIME_POINTS.items():
          suffix = tp_config['suffix']
          if col_stripped.endswith(suffix):
            patient_id = col_stripped[:-len(suffix)]
            timepoint = tp_key
            break

        if not patient_id or not timepoint:
          continue

        # Try to parse the value
        try:
          abundance = float(row[col])

          # Get or create BrackenResult
          bracken_result = BrackenResult.query.filter_by(
              user_id=user.id,
              patient_id=patient_id,
              taxonomy_id=taxonomy_id
          ).first()

          if not bracken_result:
            bracken_result = BrackenResult(
                user_id=user.id,
                patient_id=patient_id,
                taxonomy_id=taxonomy_id
            )
            db.session.add(bracken_result)

          # Set the abundance value
          if timepoint == 'pre':
            bracken_result.abundance_pre = abundance
          elif timepoint == 'during':
            bracken_result.abundance_during = abundance
          elif timepoint == 'post':
            bracken_result.abundance_post = abundance

          # Calculate deltas
          bracken_result.calculate_deltas()

          row_has_data = True
          print(
              f"  Added: Patient {patient_id}, Taxonomy {taxonomy_id}, {timepoint}={abundance}")

        except (ValueError, TypeError) as e:
          print(f"  Skipped non-numeric value: {row[col]} (error: {e})")
          continue

      if row_has_data:
        records_added += 1
        # Commit each taxonomy separately
        try:
          db.session.commit()
        except Exception as e:
          print(f"  Error committing: {e}")
          db.session.rollback()

    print(f"\nProcessed {rows_processed} rows")
    print(f"Added data for {records_added} taxonomies")

    # Check final count
    final_count = BrackenResult.query.filter_by(user_id=user.id).count()
    print(f"Final BrackenResult count in database: {final_count}")

    # Show some examples
    if final_count > 0:
      examples = BrackenResult.query.filter_by(user_id=user.id).limit(5).all()
      print(f"\nExample records:")
      for br in examples:
        print(f"  Patient {br.patient_id}, Taxonomy {br.taxonomy_id}: "
              f"pre={br.abundance_pre}, during={br.abundance_during}, post={br.abundance_post}")


if __name__ == '__main__':
  test_bracken_import()
