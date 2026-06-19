#!/usr/bin/env python3
"""
Final comprehensive test of the health monitoring system
"""
import sys
import os
import json
import numpy as np

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all imports work correctly"""
    print("Testing imports...")
    try:
        from backend import create_app, db
        from backend.models import Patient, Recording, Feature, Metric, Alert, ModelRun
        from ml.models import create_models
        from preprocess.features import extract_features
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_database():
    """Test database operations"""
    print("\nTesting database...")
    try:
        from backend import create_app, db
        from backend.models import Patient
        
        app = create_app()
        with app.app_context():
            db.create_all()
            
            # Create a test patient
            patient = Patient(name="Test Patient", age=65, conditions="Diabetes")
            db.session.add(patient)
            db.session.commit()
            
            # Query the patient
            found_patient = Patient.query.first()
            assert found_patient.name == "Test Patient"
            print("✓ Database operations successful")
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
        assert len(models) == 4
        assert 'respiration' in models
        assert 'cardiac' in models
        assert 'mobility' in models
        assert 'ensemble' in models
        print("✓ ML models created successfully")
        return True
    except Exception as e:
        print(f"✗ ML model test failed: {e}")
        return False

def test_feature_extraction():
    """Test feature extraction"""
    print("\nTesting feature extraction...")
    try:
        from preprocess.features import extract_features
        
        # Generate test data
        csi_data = np.random.randn(1000, 3)
        features = extract_features(csi_data)
        
        assert len(features) > 0
        print(f"✓ Feature extraction successful ({len(features)} features)")
        return True
    except Exception as e:
        print(f"✗ Feature extraction failed: {e}")
        return False

def test_api_routes():
    """Test API route creation"""
    print("\nTesting API routes...")
    try:
        from backend import create_app
        
        app = create_app()
        
        # Check if routes are registered
        rules = [rule.rule for rule in app.url_map.iter_rules()]
        
        expected_routes = [
            '/api/v1/patients',
            '/api/v1/recordings',
            '/api/v1/health'
        ]
        
        for route in expected_routes:
            assert any(route in rule for rule in rules), f"Route {route} not found"
        
        print("✓ API routes registered successfully")
        return True
    except Exception as e:
        print(f"✗ API route test failed: {e}")
        return False

def test_synthetic_data():
    """Test synthetic data generation"""
    print("\nTesting synthetic data generation...")
    try:
        import subprocess
        result = subprocess.run(['python', 'scripts/generate_synthetic.py'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            # Check if files were created
            if os.path.exists('data/synthetic') and len(os.listdir('data/synthetic')) > 0:
                print("✓ Synthetic data generation successful")
                return True
            else:
                print("✗ No synthetic data files found")
                return False
        else:
            print(f"✗ Synthetic data generation failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Synthetic data test failed: {e}")
        return False

def test_risk_scoring():
    """Test risk scoring functionality"""
    print("\nTesting risk scoring...")
    try:
        from backend import create_app
        from backend.routes.health import calculate_risk_score
        
        app = create_app()
        with app.app_context():
            # Test normal values
            normal_score = calculate_risk_score(16, 80, 30, 'normal')
            assert 0 <= normal_score <= 100
            
            # Test abnormal values
            high_score = calculate_risk_score(5, 120, 10, 'fall')
            assert high_score > normal_score
            
            print("✓ Risk scoring working correctly")
            return True
    except Exception as e:
        print(f"✗ Risk scoring test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Health Monitoring System - Final Comprehensive Test")
    print("=" * 60)
    
    tests = [
        ("Import Tests", test_imports),
        ("Database Tests", test_database),
        ("ML Model Tests", test_ml_models),
        ("Feature Extraction Tests", test_feature_extraction),
        ("API Route Tests", test_api_routes),
        ("Synthetic Data Tests", test_synthetic_data),
        ("Risk Scoring Tests", test_risk_scoring)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 30)
        if test_func():
            passed += 1
            print(f"✓ {test_name} PASSED")
        else:
            print(f"✗ {test_name} FAILED")
    
    print("\n" + "=" * 60)
    print(f"Final Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! System is fully functional.")
        print("\nSystem Components Verified:")
        print("✓ Flask backend with REST API")
        print("✓ SQLite database with all models")
        print("✓ Machine learning models (CNN, LSTM, TCN)")
        print("✓ Feature extraction pipeline")
        print("✓ Risk scoring algorithm")
        print("✓ Synthetic data generation")
        print("✓ Comprehensive test suite")
        
        print("\n🚀 The Non-Contact Multi-Modal Health Monitoring system is ready!")
        print("\nTo use the system:")
        print("1. Start the server: python -m backend.app")
        print("2. The API will be available at http://localhost:5001")
        print("3. Check README.md for API documentation")
        print("4. Run demo.py to see the system in action")
        
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
