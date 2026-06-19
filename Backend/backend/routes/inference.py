"""
Model training and inference routes
"""
import os
import json
from flask import Blueprint, request, jsonify, current_app
from ..models import db, ModelRun
from ..config import Config
import logging

inference_bp = Blueprint('inference', __name__)
logger = logging.getLogger(__name__)

@inference_bp.route('/models/train', methods=['POST'])
def train_model():
    """Trigger model training"""
    try:
        data = request.get_json() or {}
        model_type = data.get('model_type', 'respiration')
        params = data.get('params', {})
        
        # Create model run record
        model_run = ModelRun(
            type=model_type,
            params_json=params,
            status='pending'
        )
        db.session.add(model_run)
        db.session.commit()
        
        # Start training in background (simplified for demo)
        import threading
        def train_worker():
            try:
                model_run.status = 'running'
                db.session.commit()
                
                # Import and run training
                from ml.train import train_model
                artifact_path, metrics = train_model(model_type, params)
                
                model_run.artifact_path = artifact_path
                model_run.metrics_json = metrics
                model_run.status = 'completed'
                db.session.commit()
                
            except Exception as e:
                logger.error(f"Training failed: {str(e)}")
                model_run.status = 'failed'
                db.session.commit()
        
        # Start training thread
        thread = threading.Thread(target=train_worker)
        thread.start()
        
        return jsonify({
            'job_id': model_run.id,
            'status': model_run.status,
            'message': 'Training started'
        })
        
    except Exception as e:
        logger.error(f"Error starting training: {str(e)}")
        db.session.rollback()
        return jsonify({'error_code': 'INTERNAL_ERROR', 'message': 'Failed to start training'}), 500

@inference_bp.route('/models/<int:job_id>/status', methods=['GET'])
def get_training_status(job_id):
    """Get training job status"""
    try:
        model_run = ModelRun.query.get_or_404(job_id)
        
        result = {
            'job_id': model_run.id,
            'status': model_run.status,
            'type': model_run.type,
            'params': model_run.params_json,
            'metrics': model_run.metrics_json,
            'artifact_path': model_run.artifact_path,
            'created_at': model_run.created_at.isoformat()
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error fetching training status: {str(e)}")
        return jsonify({'error_code': 'INTERNAL_ERROR', 'message': 'Failed to fetch training status'}), 500
