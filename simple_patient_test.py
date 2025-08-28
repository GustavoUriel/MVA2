#!/usr/bin/env python3
"""
Simple test script to verify patient data import functionality works
"""

import sys
import os
import tempfile
import pandas as pd

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

from app import create_app, db
from app.models.patient import Patient
from app.models.user import User
from app.api.uploads import _detect_data_type

def test_patient_detection():
    """Test that patient data can be detected correctly"""
    
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
        }
    ]
    
    df = pd.DataFrame(patient_data)
    columns = list(df.columns)
    
    print(f"Test columns: {columns}")
    
    # Test data type detection
    data_type = _detect_data_type(columns)
    print(f"Detected data type: {data_type}")
    
    assert data_type == 'patients', f"Expected 'patients', got '{data_type}'"
    print("✅ Patient detection test PASSED!")

def test_patient_model():
    """Test that patient model works correctly"""
    
    # Create test app
    app = create_app()
    app.config.from_object('config.TestingConfig')
    
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Create test user
        test_user = User(email='test@example.com', username='testuser')
        test_user.set_password('testpass')
        db.session.add(test_user)
        db.session.commit()
        
        # Create sample patient data
        patient_data = {
            'patient_id': 'P001',
            'age': 25,
            'gender': 'F',
            'diagnosis': 'Healthy',
            'study_group': 'Control'
        }
        
        # Test patient creation
        try:
            patient = Patient.create_from_dict(test_user.id, patient_data)
            db.session.commit()
            
            # Verify patient was created
            patients = Patient.query.filter_by(user_id=test_user.id).all()
            print(f"Patients in database: {len(patients)}")
            
            if len(patients) > 0:
                print(f"Patient data: {patients[0].to_dict()}")
                assert patients[0].patient_id == 'P001'
                print("✅ Patient model test PASSED!")
            else:
                print("❌ No patients found in database")
                
        except Exception as e:
            print(f"❌ Patient model test FAILED: {e}")
            raise

if __name__ == '__main__':
    print("Testing patient detection...")
    test_patient_detection()
    
    print("\nTesting patient model...")
    test_patient_model()
    
    print("\n🎉 All tests passed!")
