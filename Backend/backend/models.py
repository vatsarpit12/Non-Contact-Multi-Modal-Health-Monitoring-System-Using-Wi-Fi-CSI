"""
Database models for the health monitoring application
"""
from datetime import datetime
from backend import db
from sqlalchemy import JSON

class Patient(db.Model):
    """Patient model for storing patient information"""
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date, nullable=True)
    age = db.Column(db.Integer, nullable=True)
    conditions = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    recordings = db.relationship('Recording', backref='patient', lazy=True)
    alerts = db.relationship('Alert', backref='patient', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'dob': self.dob.isoformat() if self.dob else None,
            'age': self.age,
            'conditions': self.conditions,
            'created_at': self.created_at.isoformat()
        }

class Recording(db.Model):
    """Recording model for storing CSI data recordings"""
    __tablename__ = 'recordings'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    path = db.Column(db.String(255), nullable=False)
    device_id = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    processed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    features = db.relationship('Feature', backref='recording', lazy=True)
    metrics = db.relationship('Metric', backref='recording', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'path': self.path,
            'device_id': self.device_id,
            'timestamp': self.timestamp.isoformat(),
            'processed': self.processed,
            'created_at': self.created_at.isoformat()
        }

class Feature(db.Model):
    """Feature model for storing extracted features"""
    __tablename__ = 'features'
    
    id = db.Column(db.Integer, primary_key=True)
    recording_id = db.Column(db.Integer, db.ForeignKey('recordings.id'), nullable=False)
    feature_json = db.Column(JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'recording_id': self.recording_id,
            'feature_json': self.feature_json,
            'created_at': self.created_at.isoformat()
        }

class Metric(db.Model):
    """Metric model for storing health metrics"""
    __tablename__ = 'metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    recording_id = db.Column(db.Integer, db.ForeignKey('recordings.id'), nullable=False)
    respiration_rate = db.Column(db.Float, nullable=True)
    heart_rate = db.Column(db.Float, nullable=True)
    hrv = db.Column(db.Float, nullable=True)
    activity_label = db.Column(db.String(50), nullable=True)
    risk_score = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'recording_id': self.recording_id,
            'respiration_rate': self.respiration_rate,
            'heart_rate': self.heart_rate,
            'hrv': self.hrv,
            'activity_label': self.activity_label,
            'risk_score': self.risk_score,
            'created_at': self.created_at.isoformat()
        }

class Alert(db.Model):
    """Alert model for storing health alerts"""
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    metric_id = db.Column(db.Integer, db.ForeignKey('metrics.id'), nullable=True)
    level = db.Column(db.String(20), nullable=False)  # low, medium, high
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'metric_id': self.metric_id,
            'level': self.level,
            'message': self.message,
            'created_at': self.created_at.isoformat()
        }

class ModelRun(db.Model):
    """Model run model for storing ML model training runs"""
    __tablename__ = 'model_runs'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    params_json = db.Column(JSON, nullable=False)
    metrics_json = db.Column(JSON, nullable=True)
    artifact_path = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'params_json': self.params_json,
            'metrics_json': self.metrics_json,
            'artifact_path': self.artifact_path,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }
