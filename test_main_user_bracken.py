#!/usr/bin/env python3
"""
Test Bracken import with the primary user account (aba.uriel@gmail.com)
"""

from config import BRACKEN_TIME_POINTS
import pandas as pd
from app.models.taxonomy import BrackenResult
from app.models.user import User
from app import create_app, db
import sys
import os
sys.path.insert(0, os.path.abspath('.'))


def test_bracken_for_main_user():
  """Test Bracken import for the main user account"""

  print("=== Testing Bracken Import for Main User ===")

  app = create_app()

  with app.app_context():
    # Get the main user (aba.uriel@gmail.com)
    user = User.query.filter_by(email='aba.uriel@gmail.com').first()
    if not user:
      print("Main user not found!")
      return

    print(f"Testing with user: {user.email} (ID: {user.id})")

    # Clear existing Bracken results for this user
    existing = BrackenResult.query.filter_by(user_id=user.id).count()
    if existing > 0:
      BrackenResult.query.filter_by(user_id=user.id).delete()
      db.session.commit()
      print(f"Cleared {existing} existing BrackenResult records")

    # Load CSV and process using the same logic as the web upload
    df = pd.read_csv('instance/bracken.csv', sep=';')
    print(f"Loaded CSV with {len(df)} rows")

    records_added = 0

    # Process first 50 rows to test
    for idx, row in df.head(50).iterrows():
      taxonomy_id = str(row.iloc[0]).strip()
      if pd.isna(taxonomy_id) or taxonomy_id == '':
        continue

      row_has_data = False

      # Process each data column
      for col in df.columns[1:]:
        col_stripped = col.strip()

        if pd.isna(row[col]) or str(row[col]).strip() in ['-', '']:
          continue

        # Parse patient ID and timepoint
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

          # Set abundance value
          if timepoint == 'pre':
            bracken_result.abundance_pre = abundance
          elif timepoint == 'during':
            bracken_result.abundance_during = abundance
          elif timepoint == 'post':
            bracken_result.abundance_post = abundance

          bracken_result.calculate_deltas()
          row_has_data = True

        except (ValueError, TypeError):
          continue

      if row_has_data:
        records_added += 1
        try:
          db.session.commit()
        except Exception as e:
          print(f"Error committing: {e}")
          db.session.rollback()

    print(f"Processed {records_added} taxonomies")

    # Check final count
    final_count = BrackenResult.query.filter_by(user_id=user.id).count()
    print(f"Final BrackenResult count for {user.email}: {final_count}")

    if final_count > 0:
      examples = BrackenResult.query.filter_by(user_id=user.id).limit(3).all()
      print(f"Examples:")
      for br in examples:
        print(f"  Patient {br.patient_id}, Taxonomy {br.taxonomy_id}: "
              f"pre={br.abundance_pre}, during={br.abundance_during}, post={br.abundance_post}")


if __name__ == '__main__':
  test_bracken_for_main_user()
