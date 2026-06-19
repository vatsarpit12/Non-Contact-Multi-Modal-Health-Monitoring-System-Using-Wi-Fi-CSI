"""
Configuration settings for the health monitoring application
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API Configuration
    DEV_API_TOKEN = os.environ.get('DEV_API_TOKEN') or 'dev-token-123'
    
    # Model Configuration
    MODEL_DIR = os.environ.get('MODEL_DIR') or './models'
    
    # Risk Scoring Configuration
    RISK_WEIGHTS = {
        'respiration': 0.4,
        'cardiac': 0.4,
        'mobility': 0.2
    }
    
    RISK_THRESHOLDS = {
        'low': 30,
        'medium': 60,
        'high': 80
    }
    
    # File upload configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or './data/raw'
    
    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
