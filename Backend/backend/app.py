"""
Flask application for Non-Contact Multi-Modal Health Monitoring using Wi-Fi CSI
"""
import os
from flask import Flask
from flask_cors import CORS
from .config import Config
from .models import db
from .routes.ingest import ingest_bp
from .routes.patients import patients_bp
from .routes.inference import inference_bp
from .routes.health import health_bp

def create_app(config_class=Config):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(ingest_bp, url_prefix='/api/v1')
    app.register_blueprint(patients_bp, url_prefix='/api/v1')
    app.register_blueprint(inference_bp, url_prefix='/api/v1')
    app.register_blueprint(health_bp, url_prefix='/api/v1')
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5001)
