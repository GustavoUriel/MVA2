#!/usr/bin/env python3
"""
Check the current state of BrackenResult records in the database
"""

from app.models.taxonomy import BrackenResult
from app.models.user import User
from app import create_app, db
import sys
import os
sys.path.insert(0, os.path.abspath('.'))


def check_bracken_records():
  """Check current BrackenResult records in database"""

  print("=== Checking BrackenResult Records ===")

  app = create_app()

  with app.app_context():
    # Get all users
    users = User.query.all()
    print(f"Found {len(users)} users:")
    for user in users:
      print(f"  {user.email} (ID: {user.id})")

      # Check BrackenResult records for each user
      bracken_count = BrackenResult.query.filter_by(user_id=user.id).count()
      print(f"    BrackenResult records: {bracken_count}")

      if bracken_count > 0:
        # Show some examples
        examples = BrackenResult.query.filter_by(user_id=user.id).limit(5).all()
        print(f"    Examples:")
        for br in examples:
          print(f"      Patient {br.patient_id}, Taxonomy {br.taxonomy_id}: "
                f"pre={br.abundance_pre}, during={br.abundance_during}, post={br.abundance_post}")

    # Total count
    total_bracken = BrackenResult.query.count()
    print(f"\nTotal BrackenResult records across all users: {total_bracken}")


if __name__ == '__main__':
  check_bracken_records()
