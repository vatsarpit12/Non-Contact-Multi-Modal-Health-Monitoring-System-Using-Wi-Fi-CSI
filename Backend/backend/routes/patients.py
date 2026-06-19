"""
Patient management routes
"""
from flask import Blueprint, request, jsonify
from ..models import db, Patient, Alert
from ..config import Config
import logging

patients_bp = Blueprint('patients', __name__)
logger = logging.getLogger(__name__)

@patients_bp.route('/patients', methods=['GET', 'POST'])
def patients():
    """Get all patients or create a new patient"""
    if request.method == 'GET':
        return get_all_patients()
    else:
        return create_patient()

def get_all_patients():
    """Get all patients"""
    try:
        patients = Patient.query.all()
        return jsonify([patient.to_dict() for patient in patients])
    except Exception as e:
        logger.error(f"Error fetching patients: {str(e)}")
        return jsonify({'error_code': 'INTERNAL_ERROR', 'message': 'Failed to fetch patients'}), 500

def create_patient():
    """Create a new patient"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'name' not in data:
            return jsonify({'error_code': 'MISSING_NAME', 'message': 'Patient name is required'}), 400
        
        # Create new patient
        patient = Patient(
            name=data['name'],
            age=data.get('age'),
            conditions=data.get('conditions')
        )
        
        db.session.add(patient)
        db.session.commit()
        
        logger.info(f"Created patient {patient.id}: {patient.name}")
        return jsonify(patient.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Error creating patient: {str(e)}")
        db.session.rollback()
        return jsonify({'error_code': 'INTERNAL_ERROR', 'message': 'Failed to create patient'}), 500

@patients_bp.route('/patients/<int:patient_id>', methods=['GET'])
def get_patient(patient_id):
    """Get patient information and latest risk score"""
    try:
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({'error_code': 'PATIENT_NOT_FOUND', 'message': 'Patient not found'}), 404
        
        # Get latest risk score from metrics
        from ..models import Metric, Recording
        latest_metric = db.session.query(Metric).join(Recording).filter(
            Recording.patient_id == patient_id
        ).order_by(Metric.created_at.desc()).first()
        
        patient_data = patient.to_dict()
        if latest_metric:
            patient_data['latest_risk_score'] = latest_metric.risk_score
            patient_data['latest_metrics'] = latest_metric.to_dict()
        
        return jsonify(patient_data)
        
    except Exception as e:
        logger.error(f"Error fetching patient {patient_id}: {str(e)}")
        return jsonify({'error_code': 'INTERNAL_ERROR', 'message': 'Failed to fetch patient'}), 500

@patients_bp.route('/patients/<int:patient_id>/alerts', methods=['GET'])
def get_patient_alerts(patient_id):
    """Get active alerts and historical warnings for a patient"""
    try:
        # Check if patient exists
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({'error_code': 'PATIENT_NOT_FOUND', 'message': 'Patient not found'}), 404
        
        # Get all alerts for the patient
        alerts = Alert.query.filter_by(patient_id=patient_id).order_by(Alert.created_at.desc()).all()
        
        return jsonify([alert.to_dict() for alert in alerts])
        
    except Exception as e:
        logger.error(f"Error fetching alerts for patient {patient_id}: {str(e)}")
        return jsonify({'error_code': 'INTERNAL_ERROR', 'message': 'Failed to fetch alerts'}), 500
