"""
Health monitoring and risk scoring routes
"""
from flask import Blueprint, request, jsonify, current_app
from ..models import db, Patient, Metric, Alert
from ..config import Config
from sqlalchemy import text
import logging

health_bp = Blueprint('health', __name__)
logger = logging.getLogger(__name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint"""
    try:
        # Check database connectivity
        db.session.execute(text('SELECT 1'))
        
        # Check if model artifacts exist
        import os
        model_dir = current_app.config['MODEL_DIR']
        model_exists = os.path.exists(model_dir) and len(os.listdir(model_dir)) > 0
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'models_available': model_exists,
            'version': '1.0.0'
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

def calculate_risk_score(respiration_rate, heart_rate, hrv, activity_label):
    """Calculate risk score based on health metrics"""
    config = current_app.config
    
    # Normalize metrics to 0-100 scale
    def normalize_respiration(rate):
        if rate is None:
            return 50  # Neutral score
        # Normal range: 12-20 breaths/min
        if 12 <= rate <= 20:
            return 0
        elif rate < 12 or rate > 20:
            return min(100, abs(rate - 16) * 5)  # Penalty for deviation
    
    def normalize_heart_rate(rate):
        if rate is None:
            return 50  # Neutral score
        # Normal range: 60-100 bpm
        if 60 <= rate <= 100:
            return 0
        elif rate < 60 or rate > 100:
            return min(100, abs(rate - 80) * 2)  # Penalty for deviation
    
    def normalize_hrv(hrv_value):
        if hrv_value is None:
            return 50  # Neutral score
        # Higher HRV is generally better
        if hrv_value > 30:
            return 0
        else:
            return min(100, (30 - hrv_value) * 3)  # Penalty for low HRV
    
    def normalize_activity(activity):
        if activity is None:
            return 50  # Neutral score
        # Penalize concerning activities
        concerning_activities = ['fall', 'unconscious', 'seizure']
        if activity.lower() in concerning_activities:
            return 100
        elif activity.lower() == 'normal':
            return 0
        else:
            return 25  # Slight penalty for unusual activity
    
    # Calculate weighted risk score
    weights = config['RISK_WEIGHTS']
    risk_score = (
        weights['respiration'] * normalize_respiration(respiration_rate) +
        weights['cardiac'] * (normalize_heart_rate(heart_rate) + normalize_hrv(hrv)) / 2 +
        weights['mobility'] * normalize_activity(activity_label)
    )
    
    return min(100, max(0, risk_score))

def create_alert_if_needed(patient_id, metric_id, risk_score):
    """Create alert if risk score exceeds thresholds"""
    config = current_app.config
    thresholds = config['RISK_THRESHOLDS']
    
    if risk_score >= thresholds['high']:
        level = 'high'
        message = f"High risk detected: Risk score {risk_score:.1f}"
    elif risk_score >= thresholds['medium']:
        level = 'medium'
        message = f"Medium risk detected: Risk score {risk_score:.1f}"
    elif risk_score >= thresholds['low']:
        level = 'low'
        message = f"Low risk detected: Risk score {risk_score:.1f}"
    else:
        return  # No alert needed
    
    # Create alert
    alert = Alert(
        patient_id=patient_id,
        metric_id=metric_id,
        level=level,
        message=message
    )
    
    db.session.add(alert)
    db.session.commit()
    
    logger.info(f"Created {level} alert for patient {patient_id}: {message}")
