"""
Unit tests for patient management routes
"""
import pytest
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import create_app, db
from backend.models import Patient

@pytest.fixture
def app():
    """Create test app"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
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

def test_create_patient(client, auth_headers):
    """Test creating a new patient"""
    data = {
        'name': 'Test Patient',
        'age': 65,
        'conditions': 'Diabetes;Hypertension'
    }
    
    response = client.post('/api/v1/patients', 
                          json=data, 
                          headers=auth_headers)
    
    assert response.status_code == 201
    result = json.loads(response.data)
    assert result['name'] == 'Test Patient'
    assert result['age'] == 65
    assert result['conditions'] == 'Diabetes;Hypertension'
    assert 'id' in result

def test_create_patient_missing_name(client, auth_headers):
    """Test creating patient without name"""
    data = {'age': 65}
    
    response = client.post('/api/v1/patients', 
                          json=data, 
                          headers=auth_headers)
    
    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['error_code'] == 'MISSING_NAME'

def test_get_patient(client, auth_headers):
    """Test getting patient information"""
    # Create a patient first
    patient = Patient(name='Test Patient', age=65)
    db.session.add(patient)
    db.session.commit()
    
    response = client.get(f'/api/v1/patients/{patient.id}', 
                         headers=auth_headers)
    
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['name'] == 'Test Patient'
    assert result['age'] == 65

def test_get_patient_not_found(client, auth_headers):
    """Test getting non-existent patient"""
    response = client.get('/api/v1/patients/999', 
                         headers=auth_headers)
    
    assert response.status_code == 404

def test_get_patient_alerts(client, auth_headers):
    """Test getting patient alerts"""
    # Create a patient first
    patient = Patient(name='Test Patient', age=65)
    db.session.add(patient)
    db.session.commit()
    
    response = client.get(f'/api/v1/patients/{patient.id}/alerts', 
                         headers=auth_headers)
    
    assert response.status_code == 200
    result = json.loads(response.data)
    assert isinstance(result, list)
