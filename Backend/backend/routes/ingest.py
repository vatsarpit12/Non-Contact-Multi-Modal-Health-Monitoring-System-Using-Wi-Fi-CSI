"""
Data ingestion routes for CSI recordings
"""
import os
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from ..models import db, Recording, Patient, Feature, Metric
from ..config import Config
import logging

ingest_bp = Blueprint('ingest', __name__)
logger = logging.getLogger(__name__)

@ingest_bp.route('/recordings', methods=['GET'])
def list_recordings():
    """List all recordings with optional patient filter"""
    try:
        patient_id = request.args.get('patient_id', type=int)
        
        query = Recording.query
        if patient_id:
            query = query.filter_by(patient_id=patient_id)
        
        recordings = query.order_by(Recording.timestamp.desc()).all()
        
        result = []
        for recording in recordings:
            recording_dict = recording.to_dict()
            
            # Get patient information
            patient = Patient.query.get(recording.patient_id)
            if patient:
                recording_dict['patient'] = {
                    'id': patient.id,
                    'name': patient.name,
                    'age': patient.age
                }
            
            # Get metrics if processed
            if recording.processed:
                from ..models import Metric
                metric = Metric.query.filter_by(recording_id=recording.id).first()
                if metric:
                    recording_dict['metrics'] = metric.to_dict()
            
            result.append(recording_dict)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error listing recordings: {str(e)}")
        return jsonify({'error_code': 'INTERNAL_ERROR', 'message': 'Failed to list recordings'}), 500

@ingest_bp.route('/recordings', methods=['POST'])
def upload_recording():
    """Upload a CSI recording file"""
    try:
        # Validate required fields
        if 'patient_id' not in request.form:
            return jsonify({'error_code': 'MISSING_PATIENT_ID', 'message': 'Patient ID is required'}), 400
        
        if 'device_id' not in request.form:
            return jsonify({'error_code': 'MISSING_DEVICE_ID', 'message': 'Device ID is required'}), 400
        
        if 'file' not in request.files:
            return jsonify({'error_code': 'MISSING_FILE', 'message': 'Recording file is required'}), 400
        
        patient_id = int(request.form['patient_id'])
        device_id = request.form['device_id']
        file = request.files['file']
        
        # Validate patient exists
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({'error_code': 'PATIENT_NOT_FOUND', 'message': 'Patient not found'}), 404
        
        # Validate file
        if file.filename == '':
            return jsonify({'error_code': 'NO_FILE_SELECTED', 'message': 'No file selected'}), 400
        
        # Create upload directory if it doesn't exist
        upload_dir = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"recording_{patient_id}_{timestamp}_{file.filename}"
        file_path = os.path.join(upload_dir, filename)
        
        # Save file
        file.save(file_path)
        
        # Create recording record
        recording = Recording(
            patient_id=patient_id,
            path=file_path,
            device_id=device_id,
            timestamp=datetime.now(),
            processed=False
        )
        
        db.session.add(recording)
        db.session.commit()
        
        logger.info(f"Uploaded recording {recording.id} for patient {patient_id}")
        return jsonify(recording.to_dict()), 201
        
    except ValueError as e:
        logger.error(f"Invalid input: {str(e)}")
        return jsonify({'error_code': 'INVALID_INPUT', 'message': 'Invalid input format'}), 400
    except Exception as e:
        logger.error(f"Error uploading recording: {str(e)}")
        db.session.rollback()
        return jsonify({'error_code': 'INTERNAL_ERROR', 'message': 'Failed to upload recording'}), 500

@ingest_bp.route('/recordings/<int:recording_id>/process', methods=['POST'])
def process_recording(recording_id):
    """Trigger preprocessing and feature extraction for a recording"""
    try:
        recording = Recording.query.get_or_404(recording_id)
        
        if recording.processed:
            return jsonify({'error_code': 'ALREADY_PROCESSED', 'message': 'Recording already processed'}), 400
        
        # Import processing modules
        from preprocess.features import extract_features
        from ml.inference import run_inference
        
        # Load CSI data
        with open(recording.path, 'r') as f:
            if recording.path.endswith('.json'):
                data = json.load(f)
                csi_data = data.get('csi_data', data)
            else:
                # Handle CSV or other formats
                import pandas as pd
                csi_data = pd.read_csv(f).values.tolist()
        
        # Ensure csi_data is a numpy array
        import numpy as np
        csi_data = np.array(csi_data)
        
        # Extract features
        features = extract_features(csi_data)
        
        # Run inference
        metrics = run_inference(features)
        
        # Save features and metrics to database
        from ..models import Feature, Metric
        feature_record = Feature(
            recording_id=recording_id,
            feature_json=features
        )
        db.session.add(feature_record)
        
        metric_record = Metric(
            recording_id=recording_id,
            respiration_rate=metrics.get('respiration_rate'),
            heart_rate=metrics.get('heart_rate'),
            hrv=metrics.get('hrv'),
            activity_label=metrics.get('activity_label'),
            risk_score=metrics.get('risk_score')
        )
        db.session.add(metric_record)
        
        # Mark recording as processed
        recording.processed = True
        db.session.commit()
        
        logger.info(f"Processed recording {recording_id}")
        return jsonify(metric_record.to_dict())
        
    except FileNotFoundError:
        return jsonify({'error_code': 'FILE_NOT_FOUND', 'message': 'Recording file not found'}), 404
    except Exception as e:
        logger.error(f"Error processing recording {recording_id}: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        db.session.rollback()
        return jsonify({'error_code': 'INTERNAL_ERROR', 'message': f'Failed to process recording: {str(e)}'}), 500

@ingest_bp.route('/recordings/<int:recording_id>/metrics', methods=['GET'])
def get_recording_metrics(recording_id):
    """Get processed metrics for a recording"""
    try:
        recording = Recording.query.get_or_404(recording_id)
        
        if not recording.processed:
            return jsonify({'error_code': 'NOT_PROCESSED', 'message': 'Recording not yet processed'}), 400
        
        # Get features and metrics
        features = db.session.query(Feature).filter_by(recording_id=recording_id).first()
        metrics = db.session.query(Metric).filter_by(recording_id=recording_id).first()
        
        result = {
            'recording_id': recording_id,
            'features': features.to_dict() if features else None,
            'metrics': metrics.to_dict() if metrics else None
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error fetching metrics for recording {recording_id}: {str(e)}")
        return jsonify({'error_code': 'INTERNAL_ERROR', 'message': 'Failed to fetch metrics'}), 500

@ingest_bp.route('/patients/<int:patient_id>/metrics', methods=['GET'])
def get_patient_metrics(patient_id):
    """Get recent health metrics for a specific patient"""
    try:
        # Validate patient exists
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({'error_code': 'PATIENT_NOT_FOUND', 'message': 'Patient not found'}), 404
        
        # Get recent processed recordings for this patient
        recordings = db.session.query(Recording).filter_by(
            patient_id=patient_id, 
            processed=True
        ).order_by(Recording.timestamp.desc()).limit(5).all()
        
        result = []
        for recording in recordings:
            # Get metrics for this recording
            from ..models import Metric
            metric = Metric.query.filter_by(recording_id=recording.id).first()
            if metric:
                recording_data = {
                    'recording_id': recording.id,
                    'timestamp': recording.timestamp.isoformat() if recording.timestamp else None,
                    'device_id': recording.device_id,
                    'metrics': metric.to_dict()
                }
                result.append(recording_data)
        
        return jsonify({
            'patient_id': patient_id,
            'patient_name': patient.name,
            'recent_metrics': result
        })
        
    except Exception as e:
        logger.error(f"Error fetching metrics for patient {patient_id}: {str(e)}")
        return jsonify({'error_code': 'INTERNAL_ERROR', 'message': 'Failed to fetch patient metrics'}), 500
