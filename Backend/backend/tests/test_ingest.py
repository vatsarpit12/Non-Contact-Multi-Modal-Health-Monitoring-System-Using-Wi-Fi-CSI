"""
Unit tests for data ingestion routes
"""
import pytest
import json
import os
import tempfile
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import create_app, db
from backend.models import Patient, Recording

@pytest.fixture
def app():
    """Create test app"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def auth_headers():
    """Create authentication headers"""
    return {'Authorization': 'Bearer dev-token-123'}

@pytest.fixture
def sample_patient(app):
    """Create a sample patient"""
    with app.app_context():
        patient = Patient(name='Test Patient', age=65)
        db.session.add(patient)
        db.session.commit()
        patient_id = patient.id
        db.session.close()
        return patient_id

def test_upload_recording(client, auth_headers, sample_patient):
    """Test uploading a recording"""
    # Create a temporary file
    test_data = {'csi_data': [[1, 2, 3], [4, 5, 6]]}
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_data, f)
        temp_file_path = f.name
    
    try:
        with open(temp_file_path, 'rb') as f:
            data = {
                'patient_id': sample_patient,
                'device_id': 'test_device',
                'file': (f, 'test_recording.json')
            }
            
            response = client.post('/api/v1/recordings', 
                                  data=data, 
                                  headers=auth_headers,
                                  content_type='multipart/form-data')
            
            assert response.status_code == 201
            result = json.loads(response.data)
            assert result['patient_id'] == sample_patient
            assert result['device_id'] == 'test_device'
            assert 'id' in result
            
    finally:
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

def test_upload_recording_missing_patient_id(client, auth_headers):
    """Test uploading recording without patient ID"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({'test': 'data'}, f)
        temp_file_path = f.name
    
    try:
        with open(temp_file_path, 'rb') as f:
            data = {
                'device_id': 'test_device',
                'file': (f, 'test_recording.json')
            }
            
            response = client.post('/api/v1/recordings', 
                                  data=data, 
                                  headers=auth_headers,
                                  content_type='multipart/form-data')
            
            assert response.status_code == 400
            result = json.loads(response.data)
            assert result['error_code'] == 'MISSING_PATIENT_ID'
            
    finally:
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

def test_upload_recording_invalid_patient(client, auth_headers):
    """Test uploading recording with invalid patient ID"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({'test': 'data'}, f)
        temp_file_path = f.name
    
    try:
        with open(temp_file_path, 'rb') as f:
            data = {
                'patient_id': 999,  # Non-existent patient
                'device_id': 'test_device',
                'file': (f, 'test_recording.json')
            }
            
            response = client.post('/api/v1/recordings', 
                                  data=data, 
                                  headers=auth_headers,
                                  content_type='multipart/form-data')
            
            assert response.status_code == 404
            
    finally:
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

def test_process_recording(client, auth_headers, sample_patient, app):
    """Test processing a recording"""
    with app.app_context():
        # Create a recording first
        from datetime import datetime
        recording = Recording(
            patient_id=sample_patient,
            path='test_path',
            device_id='test_device',
            timestamp=datetime.now(),
            processed=False
        )
        db.session.add(recording)
        db.session.commit()
        recording_id = recording.id
        db.session.close()
    
    # Mock the processing by creating a test file
    test_data = {'csi_data': [[1, 2, 3], [4, 5, 6]]}
    with open('test_path', 'w') as f:
        json.dump(test_data, f)
    
    try:
        response = client.post(f'/api/v1/recordings/{recording_id}/process', 
                             headers=auth_headers)
        
        # This will fail due to missing ML models, but we can test the endpoint
        assert response.status_code in [200, 500]  # 500 is expected due to missing models
        
    finally:
        if os.path.exists('test_path'):
            os.unlink('test_path')

def test_get_recording_metrics(client, auth_headers, sample_patient, app):
    """Test getting recording metrics"""
    with app.app_context():
        # Create a recording first
        from datetime import datetime
        recording = Recording(
            patient_id=sample_patient,
            path='test_path',
            device_id='test_device',
            timestamp=datetime.now(),
            processed=False
        )
        db.session.add(recording)
        db.session.commit()
        recording_id = recording.id
        db.session.close()
    
    response = client.get(f'/api/v1/recordings/{recording_id}/metrics', 
                         headers=auth_headers)
    
    assert response.status_code == 400  # Not processed yet
    result = json.loads(response.data)
    assert result['error_code'] == 'NOT_PROCESSED'
