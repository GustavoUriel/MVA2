#!/usr/bin/env python3
"""
Test script to verify patient data import functionality
"""

import os
import tempfile
import pandas as pd
from app import create_app, db
from app.models.patient import Patient
from app.models.user import User
from flask_login import login_user
import json


def test_patient_import():
    """Test that patient data can be imported and saved to database"""
    
    # Create test app
    app = create_app()
    app.config.from_object('config.TestingConfig')
    
    with app.app_context():
        # Create test user
        test_user = User(email='test@example.com', username='testuser')
        test_user.set_password('testpass')
        db.session.add(test_user)
        db.session.commit()
        
        # Create sample patient data
        patient_data = [
            {
                'patient_id': 'P001',
                'age': 25,
                'gender': 'F',
                'diagnosis': 'Healthy',
                'study_group': 'Control'
            },
            {
                'patient_id': 'P002',
                'age': 30,
                'gender': 'M',
                'diagnosis': 'Disease A',
                'study_group': 'Treatment'
            },
            {
                'patient_id': 'P003',
                'age': 45,
                'gender': 'F',
                'diagnosis': 'Disease B',
                'study_group': 'Control'
            }
        ]
        
        # Create temporary CSV file
        df = pd.DataFrame(patient_data)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            csv_file = f.name
        
        try:
            # Test the client
            with app.test_client() as client:
                # Login
                with client.session_transaction() as sess:
                    sess['_user_id'] = str(test_user.id)
                    sess['_fresh'] = True
                
                # Upload file first
                with open(csv_file, 'rb') as f:
                    response = client.post('/api/v1/uploads/upload', 
                                         data={'file': (f, 'patients.csv')},
                                         content_type='multipart/form-data')
                
                print(f"Upload response: {response.status_code}")
                print(f"Upload data: {response.get_json()}")
                
                if response.status_code == 200:
                    upload_data = response.get_json()
                    file_name = upload_data.get('file_name')
                    
                    # Import the file
                    import_payload = {
                        'file_name': file_name,
                        'file_type': 'csv',
                        'selections': {}
                    }
                    
                    response = client.post('/api/v1/uploads/import',
                                         data=json.dumps(import_payload),
                                         content_type='application/json')
                    
                    print(f"Import response: {response.status_code}")
                    print(f"Import data: {response.get_json()}")
                    
                    # Check if patients were created in database
                    patients = Patient.query.filter_by(user_id=test_user.id).all()
                    print(f"Patients in database: {len(patients)}")
                    
                    for patient in patients:
                        print(f"Patient: {patient.to_dict()}")
                    
                    # Verify we have the expected number of patients
                    assert len(patients) == 3, f"Expected 3 patients, got {len(patients)}"
                    
                    # Verify patient data
                    patient_ids = [p.patient_id for p in patients]
                    assert 'P001' in patient_ids
                    assert 'P002' in patient_ids
                    assert 'P003' in patient_ids
                    
                    print("✅ Patient import test PASSED!")
                    
                else:
                    print(f"❌ Upload failed with status {response.status_code}")
                    
        finally:
            # Cleanup
            os.unlink(csv_file)
if __name__ == '__main__':
  test_patient_import()
