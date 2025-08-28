#!/usr/bin/env python3
"""
Test to verify patient import directly
"""

import os
import sys
import pandas as pd
from flask import Flask
from app import create_app, db
from app.models.patient import Patient
from app.models.user import User


def test_patient_creation():
  """Test creating a patient directly"""
  print("=== Patient Creation Test ===")

  # Create Flask app context
  app = create_app()

  with app.app_context():
    try:
      # Read the fixed CSV
      df = pd.read_csv('instance/patients.csv', sep=';')
      print(f"Successfully read CSV: {df.shape}")

      # Get or create a test user
      test_user = User.query.filter_by(email='test@example.com').first()
      if not test_user:
        test_user = User(
            username='testuser',
            email='test@example.com',
            password_hash='dummy'
        )
        db.session.add(test_user)
        db.session.commit()
        print("Created test user")

      # Clear existing patients for this user
      Patient.query.filter_by(user_id=test_user.id).delete()
      db.session.commit()
      print("Cleared existing patients")

      # Process patients one by one
      success_count = 0
      error_count = 0

      for idx, row in df.iterrows():
        try:
          row_dict = row.to_dict()

          # Skip if no patient_id
          if pd.isna(row_dict.get('patient_id')) or row_dict.get('patient_id') == '':
            continue

          # Create basic patient data with only core fields
          patient_data = {
              'user_id': test_user.id,
              'patient_id': str(row_dict.get('patient_id')).strip(),
              'age': float(row_dict.get('age')) if not pd.isna(row_dict.get('age')) else None,
              'gender': str(row_dict.get('gender')).strip() if not pd.isna(row_dict.get('gender')) else None,
              'race': str(row_dict.get('race')).strip() if not pd.isna(row_dict.get('race')) else None,
              'ethnicity': str(row_dict.get('ethnicity')).strip() if not pd.isna(row_dict.get('ethnicity')) else None,
          }

          # Only add numeric fields if they're valid
          if not pd.isna(row_dict.get('weight_kg')):
            try:
              patient_data['weight_kg'] = float(row_dict.get('weight_kg'))
            except:
              pass

          if not pd.isna(row_dict.get('height_m')):
            try:
              patient_data['height_m'] = float(row_dict.get('height_m'))
            except:
              pass

          if not pd.isna(row_dict.get('bmi')):
            try:
              patient_data['bmi'] = float(row_dict.get('bmi'))
            except:
              pass

          # Create patient
          patient = Patient(**patient_data)
          db.session.add(patient)
          success_count += 1

          if success_count <= 5:  # Show first 5
            print(
                f"  Created patient {success_count}: {patient_data['patient_id']}")

        except Exception as e:
          error_count += 1
          if error_count <= 3:  # Show first 3 errors
            print(f"  Error {error_count}: {e}")

      # Commit all patients
      db.session.commit()

      # Verify count
      total_patients = Patient.query.filter_by(user_id=test_user.id).count()
      print(f"\nResults:")
      print(f"  Success: {success_count}")
      print(f"  Errors: {error_count}")
      print(f"  Total in DB: {total_patients}")

      if total_patients > 0:
        # Show some examples
        sample_patients = Patient.query.filter_by(
            user_id=test_user.id).limit(3).all()
        print(f"\nSample patients in database:")
        for p in sample_patients:
          print(f"  ID: {p.patient_id}, Age: {p.age}, Gender: {p.gender}")

      return total_patients > 0

    except Exception as e:
      print(f"Error: {e}")
      import traceback
      traceback.print_exc()
      db.session.rollback()
      return False


if __name__ == '__main__':
  print("Direct Patient Import Test")
  print("=" * 30)

  if test_patient_creation():
    print("\n✅ Test passed! Patients were created in the database.")
  else:
    print("\n❌ Test failed!")
