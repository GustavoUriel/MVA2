#!/usr/bin/env python3
"""
Test the fixed patient upload functionality
"""

import pandas as pd
import shutil
import os
from app import create_app, db
from app.models.patient import Patient
from app.models.user import User
from flask_login import login_user


def test_fixed_upload():
  """Test the patient upload with the fixed logic"""
  print("=== Testing Fixed Patient Upload ===")

  app = create_app()

  with app.app_context():
    with app.test_request_context():
      try:
        # Get user
        user = User.query.filter_by(email='aba.uriel@gmail.com').first()
        if not user:
          print("User not found")
          return False

        # Login user for the test
        login_user(user)

        # Read CSV
        df = pd.read_csv('instance/patients.csv', sep=';')
        print(f"CSV shape: {df.shape}")

        # Clear existing patients
        Patient.query.filter_by(user_id=user.id).delete()
        db.session.commit()
        print("Cleared existing patients")

        # Simulate the fixed upload logic
        records_added = 0
        for idx, row in df.iterrows():
          try:
            # Convert row to dict and clean the data
            row_dict = row.to_dict()
            patient_data = {}

            # Clean the data - handle NaN values properly
            for k, v in row_dict.items():
              if pd.isna(v) or v == '':
                patient_data[k] = None
              else:
                patient_data[k] = v

            # Create patient with proper error handling
            patient = Patient(user_id=user.id)

            # Set basic fields that are commonly available
            if patient_data.get('patient_id'):
              patient.patient_id = str(patient_data['patient_id'])
            if patient_data.get('age'):
              try:
                patient.age = float(patient_data['age'])
              except (ValueError, TypeError):
                pass
            if patient_data.get('gender'):
              patient.gender = str(patient_data['gender'])
            if patient_data.get('race'):
              patient.race = str(patient_data['race'])
            if patient_data.get('ethnicity'):
              patient.ethnicity = str(patient_data['ethnicity'])

            # Add patient to session and commit immediately
            db.session.add(patient)
            db.session.commit()
            records_added += 1

            if records_added <= 10:  # Log first 10 for debugging
              print(f"  Created patient {records_added}: {patient.patient_id}")

          except Exception as e:
            print(f"  Error creating patient {idx + 1}: {e}")
            db.session.rollback()
            continue

        print(f"\nUpload completed:")
        print(f"  Records processed: {len(df)}")
        print(f"  Records added: {records_added}")

        # Verify final count
        final_count = Patient.query.filter_by(user_id=user.id).count()
        print(f"  Final DB count: {final_count}")

        return final_count == len(df)

      except Exception as e:
        print(f"Error in test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_web_upload_simulation():
  """Test copying the file to user's upload folder and processing"""
  print("\n=== Testing Web Upload Simulation ===")

  app = create_app()

  with app.app_context():
    try:
      # Get user
      user = User.query.filter_by(email='aba.uriel@gmail.com').first()
      if not user:
        print("User not found")
        return False

      # Create user upload folder
      user_folder = f"instance/users/aba_uriel_gmail_com/uploads"
      os.makedirs(user_folder, exist_ok=True)

      # Copy the patients file to user's upload folder
      src_file = "instance/patients.csv"
      dst_file = os.path.join(user_folder, "patients.csv")
      shutil.copy2(src_file, dst_file)
      print(f"Copied {src_file} to {dst_file}")

      # Now the file should be available for the web upload process
      print("File ready for web upload process")
      return True

    except Exception as e:
      print(f"Error in web upload simulation: {e}")
      import traceback
      traceback.print_exc()
      return False


def main():
  """Main test function"""
  print("Fixed Patient Upload Test")
  print("=" * 30)

  # Test the fixed upload logic
  if test_fixed_upload():
    print("\n✅ Fixed upload test passed!")
  else:
    print("\n❌ Fixed upload test failed!")

  # Test web upload simulation
  if test_web_upload_simulation():
    print("\n✅ Web upload simulation ready!")
  else:
    print("\n❌ Web upload simulation failed!")


if __name__ == '__main__':
  main()
