#!/usr/bin/env python3
"""
Test the fixed create_from_dict method
"""

import pandas as pd
from app import create_app, db
from app.models.patient import Patient
from app.models.user import User


def test_create_from_dict():
  """Test the create_from_dict method with real CSV data"""
  print("=== Testing create_from_dict method ===")

  app = create_app()

  with app.app_context():
    try:
      # Read CSV data
      df = pd.read_csv('instance/patients.csv', sep=';')
      print(f"CSV loaded: {df.shape}")

      # Get test user
      test_user = User.query.filter_by(email='test@example.com').first()
      if not test_user:
        test_user = User(
            username='testuser',
            email='test@example.com',
            password_hash='dummy'
        )
        db.session.add(test_user)
        db.session.commit()

      # Clear existing patients
      Patient.query.filter_by(user_id=test_user.id).delete()
      db.session.commit()
      print("Cleared existing patients")

      # Test with first row
      first_row = df.iloc[0].to_dict()
      print(f"Testing with patient: {first_row.get('patient_id')}")

      # Use the create_from_dict method
      patient = Patient.create_from_dict(test_user.id, first_row)
      print(f"✅ Successfully created patient: {patient.patient_id}")

      # Verify in database
      saved_patient = Patient.query.filter_by(
          user_id=test_user.id,
          patient_id=patient.patient_id
      ).first()

      if saved_patient:
        print(f"✅ Patient verified in database")
        print(f"   ID: {saved_patient.patient_id}")
        print(f"   Age: {saved_patient.age}")
        print(f"   Gender: {saved_patient.gender}")
        print(f"   Race: {saved_patient.race}")
        return True
      else:
        print("❌ Patient not found in database")
        return False

    except Exception as e:
      print(f"❌ Error: {e}")
      import traceback
      traceback.print_exc()
      db.session.rollback()
      return False


def test_bulk_create():
  """Test bulk creation using create_from_dict"""
  print("\n=== Testing bulk creation ===")

  app = create_app()

  with app.app_context():
    try:
      # Read CSV
      df = pd.read_csv('instance/patients.csv', sep=';')

      # Get test user
      test_user = User.query.filter_by(email='test@example.com').first()

      # Clear existing patients
      Patient.query.filter_by(user_id=test_user.id).delete()
      db.session.commit()

      # Test with first 5 rows
      success_count = 0
      for idx in range(min(5, len(df))):
        try:
          row_data = df.iloc[idx].to_dict()
          patient = Patient.create_from_dict(test_user.id, row_data)
          success_count += 1
          print(f"  Created patient {success_count}: {patient.patient_id}")
        except Exception as e:
          print(f"  Error creating patient {idx + 1}: {e}")

      # Verify total count
      total_count = Patient.query.filter_by(user_id=test_user.id).count()
      print(f"\nTotal patients in database: {total_count}")

      return total_count > 0

    except Exception as e:
      print(f"❌ Bulk test error: {e}")
      return False


if __name__ == '__main__':
  print("Testing Fixed Patient Import Methods")
  print("=" * 40)

  # Test single creation
  if test_create_from_dict():
    print("\n✅ create_from_dict test passed!")
  else:
    print("\n❌ create_from_dict test failed!")
    exit(1)

  # Test bulk creation
  if test_bulk_create():
    print("\n✅ Bulk creation test passed!")
    print("\n🎉 All tests passed! Patient import should now work.")
  else:
    print("\n❌ Bulk creation test failed!")
