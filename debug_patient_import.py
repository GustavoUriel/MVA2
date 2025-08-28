#!/usr/bin/env python3
"""
Debug script to test patient CSV import functionality
"""

import os
import sys
import pandas as pd
import csv
from flask import Flask
from app import create_app, db
from app.models.patient import Patient
from app.models.user import User
from config import Config


def analyze_csv_structure():
  """Analyze the CSV file structure"""
  print("=== Analyzing CSV Structure ===")

  csv_path = 'instance/patients.csv'

  # Check if file exists
  if not os.path.exists(csv_path):
    print(f"Error: {csv_path} not found")
    return None

  # Read raw CSV structure
  with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.reader(f, delimiter=';')
    rows = list(reader)

  print(f"Total rows: {len(rows)}")
  print(f"Header fields: {len(rows[0])}")
  print(f"First data row fields: {len(rows[1]) if len(rows) > 1 else 'N/A'}")

  # Check field count consistency
  field_counts = [len(row) for row in rows]
  unique_counts = set(field_counts)

  print(f"Unique field counts: {unique_counts}")

  if len(unique_counts) > 1:
    print("WARNING: Inconsistent field counts detected!")
    for count in unique_counts:
      row_nums = [i for i, c in enumerate(field_counts) if c == count]
      print(
          f"  {count} fields: rows {row_nums[:5]}{'...' if len(row_nums) > 5 else ''}")

  return rows


def fix_csv_structure():
  """Fix the CSV structure by padding missing fields"""
  print("\n=== Fixing CSV Structure ===")

  csv_path = 'instance/patients.csv'
  backup_path = 'instance/patients_backup.csv'

  # Read the raw CSV
  with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.reader(f, delimiter=';')
    rows = list(reader)

  if not rows:
    print("Error: Empty CSV file")
    return False

  # Backup original file
  with open(backup_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f, delimiter=';')
    writer.writerows(rows)
  print(f"Backup created: {backup_path}")

  # Find the maximum number of fields
  max_fields = max(len(row) for row in rows)
  print(f"Maximum fields found: {max_fields}")

  # Pad all rows to have the same number of fields
  fixed_rows = []
  for i, row in enumerate(rows):
    if len(row) < max_fields:
      # Pad with empty strings
      padded_row = row + [''] * (max_fields - len(row))
      fixed_rows.append(padded_row)
      if i < 5:  # Show details for first few rows
        print(f"Row {i}: padded from {len(row)} to {len(padded_row)} fields")
    else:
      fixed_rows.append(row)

  # Write the fixed CSV
  with open(csv_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f, delimiter=';')
    writer.writerows(fixed_rows)

  print(f"Fixed CSV saved to: {csv_path}")
  return True


def test_patient_creation():
  """Test creating a patient from CSV data"""
  print("\n=== Testing Patient Creation ===")

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

      # Try to create a patient from the first row
      first_row = df.iloc[0].to_dict()
      print(f"First row data: {list(first_row.keys())[:10]}...")

      # Clean the data - convert NaN to None
      cleaned_data = {}
      for key, value in first_row.items():
        if pd.isna(value):
          cleaned_data[key] = None
        else:
          cleaned_data[key] = value

      # Create patient using the model method
      patient = Patient.create_from_dict(test_user.id, cleaned_data)
      print(f"Successfully created patient: {patient.patient_id}")

      # Verify patient was saved
      saved_patient = Patient.query.filter_by(user_id=test_user.id).first()
      if saved_patient:
        print(f"Patient verified in database: {saved_patient.patient_id}")
        return True
      else:
        print("Error: Patient not found in database")
        return False

    except Exception as e:
      print(f"Error testing patient creation: {e}")
      import traceback
      traceback.print_exc()
      return False


def main():
  """Main debug function"""
  print("Patient CSV Import Debug Tool")
  print("=" * 40)

  # Step 1: Analyze CSV structure
  rows = analyze_csv_structure()
  if not rows:
    return

  # Step 2: Fix CSV structure if needed
  field_counts = [len(row) for row in rows]
  if len(set(field_counts)) > 1:
    if fix_csv_structure():
      print("\nCSV structure fixed!")
    else:
      print("\nError fixing CSV structure")
      return
  else:
    print("\nCSV structure is consistent")

  # Step 3: Test patient creation
  if test_patient_creation():
    print("\n✅ Patient creation test passed!")
  else:
    print("\n❌ Patient creation test failed!")


if __name__ == '__main__':
  main()
