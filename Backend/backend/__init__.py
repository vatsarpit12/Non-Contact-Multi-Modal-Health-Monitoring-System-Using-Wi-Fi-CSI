"""
Backend package for health monitoring application
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app(config_class=None):
    """Create and configure the Flask application"""
    from backend.config import Config
    from backend.app import create_app as _create_app
    
    if config_class is None:
        config_class = Config
    
    return _create_app(config_class)
