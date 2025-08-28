#!/usr/bin/env python3
"""
Test Bracken microbiome data import functionality
"""

import pandas as pd
import os
from app import create_app, db
from app.models.taxonomy import BrackenResult
from app.models.user import User
from config import BRACKEN_TIME_POINTS


def test_bracken_data_structure():
  """Test reading and understanding the Bracken CSV structure"""
  print("=== Testing Bracken Data Structure ===")

  try:
    # Read the Bracken CSV file
    df = pd.read_csv('instance/bracken.csv', sep=';')
    print(f"Bracken CSV shape: {df.shape}")

    # Check the columns
    print(f"Total columns: {len(df.columns)}")
    print(f"First column (taxonomy): {df.columns[0]}")
    print(f"Sample columns: {list(df.columns[1:11])}")

    # Check timepoint suffixes
    print("\nTimepoint analysis:")
    for tp_key, tp_config in BRACKEN_TIME_POINTS.items():
      suffix = tp_config['suffix']
      matching_cols = [col for col in df.columns if col.endswith(suffix)]
      print(f"  {tp_key} ({suffix}): {len(matching_cols)} columns")
      if matching_cols[:3]:
        print(f"    Examples: {matching_cols[:3]}")

    # Check data content
    print(f"\nFirst few taxonomy IDs: {df.iloc[:5, 0].tolist()}")

    # Check for non-dash values
    non_dash_count = 0
    for col in df.columns[1:]:
      non_dash_values = df[col][df[col] != '-'].dropna()
      if len(non_dash_values) > 0:
        non_dash_count += len(non_dash_values)

    print(f"Total non-dash abundance values: {non_dash_count}")

    return True

  except Exception as e:
    print(f"Error reading Bracken data: {e}")
    import traceback
    traceback.print_exc()
    return False


def test_bracken_import():
  """Test importing Bracken data"""
  print("\n=== Testing Bracken Import ===")

  app = create_app()

  with app.app_context():
    try:
      # Get user
      user = User.query.filter_by(email='aba.uriel@gmail.com').first()
      if not user:
        print("User not found")
        return False

      # Clear existing Bracken data
      BrackenResult.query.filter_by(user_id=user.id).delete()
      db.session.commit()
      print("Cleared existing Bracken data")

      # Read Bracken CSV
      df = pd.read_csv('instance/bracken.csv', sep=';')
      print(f"Processing {df.shape[0]} taxonomies...")

      records_added = 0
      taxonomy_col = df.columns[0]  # First column should be taxonomy_id

      # Process first 10 rows for testing
      for idx, row in df.head(10).iterrows():
        try:
          taxonomy_id = row[taxonomy_col]
          if pd.isna(taxonomy_id) or str(taxonomy_id).strip() == '':
            continue

          print(f"Processing taxonomy {taxonomy_id}")

          # Extract patient data from columns
          for col in df.columns[1:]:  # Skip taxonomy column
            if pd.isna(row[col]) or str(row[col]).strip() in ['-', '']:
              continue

            # Parse patient ID and timepoint from column name
            patient_id = None
            timepoint = None

            # Check for each timepoint suffix
            for tp_key, tp_config in BRACKEN_TIME_POINTS.items():
              suffix = tp_config['suffix']
              if col.endswith(suffix):
                patient_id = col[:-len(suffix)]
                timepoint = tp_key
                break

            if not patient_id or not timepoint:
              continue

            # Get or create BrackenResult for this patient-taxonomy combination
            bracken_result = BrackenResult.query.filter_by(
                user_id=user.id,
                patient_id=patient_id,
                taxonomy_id=str(taxonomy_id)
            ).first()

            if not bracken_result:
              bracken_result = BrackenResult(
                  user_id=user.id,
                  patient_id=patient_id,
                  taxonomy_id=str(taxonomy_id)
              )
              db.session.add(bracken_result)

            # Set abundance value for the appropriate timepoint
            try:
              abundance = float(row[col])
              if timepoint == 'pre':
                bracken_result.abundance_pre = abundance
              elif timepoint == 'during':
                bracken_result.abundance_during = abundance
              elif timepoint == 'post':
                bracken_result.abundance_post = abundance

              # Calculate deltas when we have multiple timepoints
              bracken_result.calculate_deltas()

              print(f"  {patient_id} {timepoint}: {abundance}")

            except (ValueError, TypeError):
              # Skip non-numeric values
              continue

          # Commit after each taxonomy
          db.session.commit()
          records_added += 1

        except Exception as e:
          print(f"Error processing taxonomy {taxonomy_id}: {e}")
          db.session.rollback()
          continue

      # Check final results
      total_results = BrackenResult.query.filter_by(user_id=user.id).count()
      print(f"\nImport completed:")
      print(f"  Taxonomies processed: {records_added}")
      print(f"  Total BrackenResults created: {total_results}")

      # Show some examples
      examples = BrackenResult.query.filter_by(user_id=user.id).limit(5).all()
      print(f"\nExample results:")
      for br in examples:
        print(f"  {br.patient_id} - {br.taxonomy_id}: pre={br.abundance_pre}, during={br.abundance_during}, post={br.abundance_post}")

      return total_results > 0

    except Exception as e:
      print(f"Error in Bracken import test: {e}")
      import traceback
      traceback.print_exc()
      return False


def test_bracken_detection():
  """Test if Bracken data type detection works"""
  print("\n=== Testing Bracken Detection ===")

  try:
    # Read the CSV and check columns
    df = pd.read_csv('instance/bracken.csv', sep=';')
    columns = list(df.columns)

    # Check if detection logic would work
    suffixes = [cfg['suffix'] for cfg in BRACKEN_TIME_POINTS.values()]
    print(f"Looking for suffixes: {suffixes}")

    detected = any(any(col.endswith(suf) for suf in suffixes)
                   for col in columns)
    print(f"Bracken detection result: {detected}")

    if detected:
      matching_columns = [col for col in columns if any(
          col.endswith(suf) for suf in suffixes)]
      print(f"Matching columns: {len(matching_columns)}")
      print(f"Examples: {matching_columns[:5]}")

    return detected

  except Exception as e:
    print(f"Error in detection test: {e}")
    return False


def main():
  """Main test function"""
  print("Bracken Import Test")
  print("=" * 30)

  # Test data structure
  if test_bracken_data_structure():
    print("\n✅ Data structure test passed!")
  else:
    print("\n❌ Data structure test failed!")
    return

  # Test detection
  if test_bracken_detection():
    print("\n✅ Detection test passed!")
  else:
    print("\n❌ Detection test failed!")
    return

  # Test import
  if test_bracken_import():
    print("\n✅ Import test passed!")
  else:
    print("\n❌ Import test failed!")


if __name__ == '__main__':
  main()
