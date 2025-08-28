#!/usr/bin/env python3
"""
Test the patient creation process to find where it's failing
"""

import pandas as pd
from app import create_app, db
from app.models.patient import Patient
from app.models.user import User


def test_individual_patients():
  """Test creating each patient individually to find the failure point"""
  print("=== Testing Individual Patient Creation ===")

  app = create_app()

  with app.app_context():
    try:
      # Read CSV
      df = pd.read_csv('instance/patients.csv', sep=';')

      # Get test user
      test_user = User.query.filter_by(email='test@example.com').first()
      if not test_user:
        print("Test user not found")
        return

      # Clear existing patients
      Patient.query.filter_by(user_id=test_user.id).delete()
      db.session.commit()

      success_count = 0
      error_count = 0

      for idx, row in df.iterrows():
        try:
          print(f"\nTesting row {idx + 1}: {row['patient_id']}")

          # Original logic from uploads.py - filter out NaN values
          patient_data_filtered = {k: v for k,
                                   v in row.to_dict().items() if pd.notna(v)}
          print(f"  Filtered data keys: {len(patient_data_filtered)}")

          # Try to create patient using the original method
          Patient.create_from_dict(test_user.id, patient_data_filtered)

          success_count += 1
          print(f"  ✅ SUCCESS: Created patient {row['patient_id']}")

        except Exception as e:
          error_count += 1
          print(f"  ❌ ERROR: {e}")
          print(
              f"     Patient data keys: {list(patient_data_filtered.keys())[:10]}...")

          # Try to get more details about the error
          import traceback
          error_details = traceback.format_exc()
          if "required" in str(e).lower() or "null" in str(e).lower():
            print(f"     Likely missing required field error")

          # Continue to next patient
          db.session.rollback()
          continue

      print(f"\nResults:")
      print(f"  Success: {success_count}")
      print(f"  Errors: {error_count}")

      # Check what's in the database
      final_count = Patient.query.filter_by(user_id=test_user.id).count()
      print(f"  Final DB count: {final_count}")

    except Exception as e:
      print(f"Error in test: {e}")
      import traceback
      traceback.print_exc()


def test_patient_data_structure():
  """Analyze the structure of patient data to understand the issue"""
  print("\n=== Analyzing Patient Data Structure ===")

  try:
    df = pd.read_csv('instance/patients.csv', sep=';')

    # Check the 6th row (first one that fails)
    failed_row = df.iloc[5]  # ENG1018
    success_row = df.iloc[0]  # ENG1001

    print("Comparing successful vs failed row:")
    print(f"Success (ENG1001): {success_row['patient_id']}")
    print(f"Failed  (ENG1018): {failed_row['patient_id']}")

    # Compare the data
    success_data = {k: v for k, v in success_row.to_dict().items()
                    if pd.notna(v)}
    failed_data = {k: v for k, v in failed_row.to_dict().items() if pd.notna(v)}

    print(f"\nSuccess row non-null fields: {len(success_data)}")
    print(f"Failed row non-null fields: {len(failed_data)}")

    # Check specific fields
    important_fields = ['patient_id', 'age', 'gender', 'race', 'ethnicity']
    print(f"\nImportant fields comparison:")
    for field in important_fields:
      success_val = success_row.get(field)
      failed_val = failed_row.get(field)
      print(f"  {field}:")
      print(f"    Success: {success_val} (type: {type(success_val)})")
      print(f"    Failed:  {failed_val} (type: {type(failed_val)})")

    # Look for any obvious differences
    success_keys = set(success_data.keys())
    failed_keys = set(failed_data.keys())

    only_in_success = success_keys - failed_keys
    only_in_failed = failed_keys - success_keys

    if only_in_success:
      print(f"\nFields only in successful row: {only_in_success}")
    if only_in_failed:
      print(f"Fields only in failed row: {only_in_failed}")

  except Exception as e:
    print(f"Error analyzing data: {e}")
    import traceback
    traceback.print_exc()


def main():
  """Main test function"""
  print("Patient Import Debugging")
  print("=" * 30)

  # Analyze data structure first
  test_patient_data_structure()

  # Test individual patient creation
  test_individual_patients()


if __name__ == '__main__':
  main()
