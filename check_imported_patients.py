#!/usr/bin/env python3
"""
Check what patients were imported and analyze the upload issue
"""

import pandas as pd
from app import create_app, db
from app.models.patient import Patient
from app.models.user import User


def check_imported_patients():
  """Check what patients were imported"""
  print("=== Checking Imported Patients ===")

  app = create_app()

  with app.app_context():
    try:
      # Get all users and their patients
      users = User.query.all()
      print(f"Total users: {len(users)}")

      for user in users:
        patients = Patient.query.filter_by(user_id=user.id).all()
        print(f"\nUser: {user.email} ({user.username})")
        print(f"  Patient count: {len(patients)}")

        if patients:
          print("  Patient IDs:")
          for i, patient in enumerate(patients):
            print(
                f"    {i+1}. {patient.patient_id} (age: {patient.age}, gender: {patient.gender})")
            if i >= 9:  # Show first 10
              print(f"    ... and {len(patients) - 10} more")
              break

      # Check total patient count
      total_patients = Patient.query.count()
      print(f"\nTotal patients in database: {total_patients}")

      return total_patients

    except Exception as e:
      print(f"Error checking patients: {e}")
      import traceback
      traceback.print_exc()
      return 0


def check_csv_data():
  """Check the source CSV data"""
  print("\n=== Checking Source CSV Data ===")

  try:
    df = pd.read_csv('instance/patients.csv', sep=';')
    print(f"CSV contains {len(df)} rows")

    # Check for valid patient IDs
    valid_ids = df['patient_id'].dropna()
    print(f"Valid patient IDs: {len(valid_ids)}")

    # Show first few patient IDs
    print("First 10 patient IDs:")
    for i, pid in enumerate(valid_ids.head(10)):
      print(f"  {i+1}. {pid}")

    # Check for duplicates
    duplicates = valid_ids[valid_ids.duplicated()].tolist()
    if duplicates:
      print(f"Duplicate patient IDs: {duplicates}")
    else:
      print("No duplicate patient IDs found")

    return len(valid_ids)

  except Exception as e:
    print(f"Error checking CSV: {e}")
    import traceback
    traceback.print_exc()
    return 0


def analyze_upload_issue():
  """Analyze why only 5 records were imported"""
  print("\n=== Analyzing Upload Issue ===")

  app = create_app()

  with app.app_context():
    try:
      # Read CSV
      df = pd.read_csv('instance/patients.csv', sep=';')

      # Get imported patients
      patients = Patient.query.all()
      imported_ids = [p.patient_id for p in patients]

      print(f"CSV has {len(df)} rows")
      print(f"Database has {len(patients)} patients")
      print(f"Imported patient IDs: {imported_ids}")

      # Check which rows from CSV were imported
      csv_ids = df['patient_id'].dropna().tolist()
      print(f"CSV patient IDs: {csv_ids[:10]}...")

      # Find which ones were not imported
      not_imported = [pid for pid in csv_ids if pid not in imported_ids]
      print(f"Not imported ({len(not_imported)}): {not_imported[:10]}...")

      # Check for any patterns in the data that might cause issues
      print("\nAnalyzing potential issues:")

      # Check first few rows for data issues
      for i in range(min(10, len(df))):
        row = df.iloc[i]
        patient_id = row['patient_id']
        age = row['age']
        gender = row['gender']

        issues = []
        if pd.isna(patient_id) or patient_id == '':
          issues.append("missing patient_id")
        if pd.isna(age):
          issues.append("missing age")
        if pd.isna(gender) or gender == '':
          issues.append("missing gender")

        status = "IMPORTED" if patient_id in imported_ids else "NOT IMPORTED"
        print(f"  Row {i+1}: {patient_id} - {status}")
        if issues:
          print(f"    Issues: {', '.join(issues)}")

    except Exception as e:
      print(f"Error analyzing upload: {e}")
      import traceback
      traceback.print_exc()


def main():
  """Main analysis function"""
  print("Patient Import Analysis")
  print("=" * 30)

  # Check imported patients
  imported_count = check_imported_patients()

  # Check CSV data
  csv_count = check_csv_data()

  # Analyze the issue
  analyze_upload_issue()

  print(f"\nSummary:")
  print(f"  CSV rows: {csv_count}")
  print(f"  Imported: {imported_count}")
  print(f"  Missing: {csv_count - imported_count}")


if __name__ == '__main__':
  main()
