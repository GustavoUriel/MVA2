#!/usr/bin/env python3
"""
Test script to verify detailed logging functionality in MVA2.

This script creates a simple test file and simulates an upload to check
if all the detailed step-by-step logging is working correctly.
"""

import os
import requests
import json
import tempfile
import pandas as pd

def create_test_csv():
    """Create a test CSV file for upload testing."""
    test_data = {
        'patient_id': ['P001', 'P002', 'P003'],
        'age': [45, 67, 32],
        'sex': ['M', 'F', 'M'],
        'race': ['White', 'Asian', 'Black'],
        'Start_Date': ['2023-01-01', '2023-02-01', '2023-03-01'],
        'End_Date': ['2023-06-01', '2023-07-01', '2023-08-01'],
        'survival_months': [24, 18, 36]
    }
    
    df = pd.DataFrame(test_data)
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    df.to_csv(temp_file.name, index=False)
    temp_file.close()
    
    return temp_file.name

def create_test_excel():
    """Create a test Excel file for upload testing."""
    test_data = {
        'taxon_id': ['T001', 'T002', 'T003'],
        'taxonomy': ['Bacteria;Firmicutes', 'Bacteria;Bacteroidetes', 'Bacteria;Proteobacteria'],
        'abundance': [0.45, 0.32, 0.23],
        'species': ['Species A', 'Species B', 'Species C']
    }
    
    df = pd.DataFrame(test_data)
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.xlsx', delete=False)
    temp_file.close()  # Close to allow pandas to write
    
    df.to_excel(temp_file.name, index=False, engine='openpyxl')
    
    return temp_file.name

def test_upload_analyze(base_url, file_path):
    """Test the upload analyze endpoint."""
    print(f"\n=== Testing Upload Analyze with {file_path} ===")
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            
            print(f"Sending POST request to {base_url}/api/v1/uploads/analyze")
            response = requests.post(f"{base_url}/api/v1/uploads/analyze", files=files)
            
            print(f"Response Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Success! Response: {json.dumps(result, indent=2)}")
                return result
            else:
                print(f"Error Response: {response.text}")
                return None
                
    except Exception as e:
        print(f"Exception during upload test: {e}")
        return None

def test_upload_import(base_url, file_name, file_type, sheets):
    """Test the upload import endpoint."""
    print(f"\n=== Testing Upload Import ===")
    
    # Create import request based on analyze results
    selections = {}
    for sheet in sheets:
        selections[sheet['sheet_name']] = {
            'confirmed': True,
            'header_mode': sheet['header_mode'],
            'renames': sheet['proposed_renames'],
            'duplicate_keep': {name: 0 for name in sheet['duplicates'].keys()},
            'detected_type': sheet['detected_type']
        }
    
    import_data = {
        'file_name': file_name,
        'file_type': file_type,
        'selections': selections
    }
    
    try:
        print(f"Sending POST request to {base_url}/api/v1/uploads/import")
        print(f"Import data: {json.dumps(import_data, indent=2)}")
        
        response = requests.post(
            f"{base_url}/api/v1/uploads/import",
            json=import_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success! Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"Error Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"Exception during import test: {e}")
        return False

def main():
    """Main test function."""
    base_url = "http://127.0.0.1:5000"
    
    print("MVA2 Detailed Logging Test")
    print("=" * 50)
    print("\nThis test will:")
    print("1. Create test CSV and Excel files")
    print("2. Test upload analyze endpoint")
    print("3. Test upload import endpoint")
    print("4. Check for detailed logging in user log files")
    print("\nNote: You must be logged in to the application for this test to work.")
    print("Please log in via the web interface first.")
    
    input("\nPress Enter to continue...")
    
    # Create test files
    print("\n1. Creating test files...")
    csv_file = create_test_csv()
    excel_file = create_test_excel()
    
    print(f"Created CSV file: {csv_file}")
    print(f"Created Excel file: {excel_file}")
    
    # Test CSV upload
    print("\n2. Testing CSV upload...")
    csv_result = test_upload_analyze(base_url, csv_file)
    
    if csv_result:
        print("\n3. Testing CSV import...")
        test_upload_import(base_url, csv_result['file_name'], csv_result['file_type'], csv_result['sheets'])
    
    # Test Excel upload
    print("\n4. Testing Excel upload...")
    excel_result = test_upload_analyze(base_url, excel_file)
    
    if excel_result:
        print("\n5. Testing Excel import...")
        test_upload_import(base_url, excel_result['file_name'], excel_result['file_type'], excel_result['sheets'])
    
    # Cleanup
    print("\n6. Cleaning up test files...")
    try:
        os.unlink(csv_file)
        os.unlink(excel_file)
        print("Test files deleted.")
    except Exception as e:
        print(f"Error cleaning up files: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed!")
    print("\nTo check the detailed logging:")
    print("1. Look for log files in: instance/users/{your_email_prefix}/")
    print("2. Check the upload log: {email_prefix}_upload.log")
    print("3. Look for STEP-by-STEP entries showing the detailed process flow")
    print("\nThe logs should show every step of the upload and import process")
    print("with detailed information about file processing, data shapes, and outcomes.")

if __name__ == "__main__":
    main()
