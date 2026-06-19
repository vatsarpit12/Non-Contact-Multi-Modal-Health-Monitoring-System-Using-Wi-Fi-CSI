#!/usr/bin/env python3
"""
Test script to verify the setup
"""
import os
import sys
import subprocess

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        from backend import create_app, db
        print("✓ Backend imports successful")
    except Exception as e:
        print(f"✗ Backend import failed: {e}")
        return False
    
    try:
        from ml.models import create_models
        print("✓ ML models import successful")
    except Exception as e:
        print(f"✗ ML models import failed: {e}")
        return False
    
    try:
        from preprocess.features import extract_features
        print("✓ Preprocessing import successful")
    except Exception as e:
        print(f"✗ Preprocessing import failed: {e}")
        return False
    
    return True

def test_database():
    """Test database creation"""
    print("\nTesting database...")
    
    try:
        from backend import create_app, db
        app = create_app()
        
        with app.app_context():
            db.create_all()
            print("✓ Database tables created successfully")
            
            # Test basic query
            from backend.models import Patient
            patient_count = Patient.query.count()
            print(f"✓ Database query successful (patients: {patient_count})")
            
        return True
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False

def test_ml_models():
    """Test ML model creation"""
    print("\nTesting ML models...")
    
    try:
        from ml.models import create_models
        models = create_models()
        
        print(f"✓ Created {len(models)} models:")
        for name in models.keys():
            print(f"  - {name}")
        
        return True
    except Exception as e:
        print(f"✗ ML model test failed: {e}")
        return False

def test_feature_extraction():
    """Test feature extraction"""
    print("\nTesting feature extraction...")
    
    try:
        import numpy as np
        from preprocess.features import extract_features
        
        # Generate dummy CSI data
        csi_data = np.random.randn(1000, 3) + 1j * np.random.randn(1000, 3)
        
        # Extract features
        features = extract_features(csi_data)
        
        print(f"✓ Feature extraction successful ({len(features)} features)")
        
        return True
    except Exception as e:
        print(f"✗ Feature extraction test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Health Monitoring System Setup Test")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_database,
        test_ml_models,
        test_feature_extraction
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed! System is ready.")
        return 0
    else:
        print("✗ Some tests failed. Please check the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
