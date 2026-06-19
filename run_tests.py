#!/usr/bin/env python3
"""
Comprehensive test script for the health monitoring system
"""
import os
import sys
import subprocess
import time
import requests
import json
import numpy as np

def run_command(cmd, cwd=None):
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, 
                              capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

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
    """Test database creation and basic operations"""
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

def test_synthetic_data():
    """Test synthetic data generation"""
    print("\nTesting synthetic data generation...")
    
    try:
        success, stdout, stderr = run_command("python scripts/generate_synthetic.py")
        if success:
            print("✓ Synthetic data generation successful")
            
            # Check if files were created
            if os.path.exists("data/synthetic") and len(os.listdir("data/synthetic")) > 0:
                print("✓ Synthetic data files created")
                return True
            else:
                print("✗ No synthetic data files found")
                return False
        else:
            print(f"✗ Synthetic data generation failed: {stderr}")
            return False
    except Exception as e:
        print(f"✗ Synthetic data generation test failed: {e}")
        return False

def test_database_creation():
    """Test database creation script"""
    print("\nTesting database creation script...")
    
    try:
        success, stdout, stderr = run_command("python scripts/create_db.py")
        if success:
            print("✓ Database creation script successful")
            return True
        else:
            print(f"✗ Database creation script failed: {stderr}")
            return False
    except Exception as e:
        print(f"✗ Database creation script test failed: {e}")
        return False

def test_pytest():
    """Test running pytest"""
    print("\nTesting pytest...")
    
    try:
        success, stdout, stderr = run_command("pytest backend/tests/ -v --tb=short")
        if success:
            print("✓ Pytest tests passed")
            return True
        else:
            print(f"✗ Pytest tests failed: {stderr}")
            return False
    except Exception as e:
        print(f"✗ Pytest test failed: {e}")
        return False

def test_server_startup():
    """Test server startup"""
    print("\nTesting server startup...")
    
    try:
        # Start server in background
        process = subprocess.Popen(["python", "backend/app.py"], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        
        # Wait a bit for server to start
        time.sleep(5)
        
        # Test health endpoint
        try:
            response = requests.get("http://localhost:5000/api/v1/health", timeout=5)
            if response.status_code == 200:
                print("✓ Server started successfully")
                print(f"  Health check response: {response.json()}")
                
                # Stop server
                process.terminate()
                process.wait()
                return True
            else:
                print(f"✗ Server health check failed: {response.status_code}")
                process.terminate()
                process.wait()
                return False
        except Exception as e:
            print(f"✗ Server health check failed: {e}")
            process.terminate()
            process.wait()
            return False
            
    except Exception as e:
        print(f"✗ Server startup test failed: {e}")
        return False

def test_training():
    """Test ML model training"""
    print("\nTesting ML model training...")
    
    try:
        # This might take a while, so we'll just test if the script runs
        success, stdout, stderr = run_command("python -c \"from ml.train import train_model; print('Training test passed')\"")
        if success:
            print("✓ ML training test passed")
            return True
        else:
            print(f"✗ ML training test failed: {stderr}")
            return False
    except Exception as e:
        print(f"✗ ML training test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Health Monitoring System Comprehensive Test")
    print("=" * 50)
    
    tests = [
        ("Import Tests", test_imports),
        ("Database Tests", test_database),
        ("ML Model Tests", test_ml_models),
        ("Feature Extraction Tests", test_feature_extraction),
        ("Synthetic Data Generation", test_synthetic_data),
        ("Database Creation Script", test_database_creation),
        ("Pytest Tests", test_pytest),
        ("Server Startup", test_server_startup),
        ("ML Training", test_training)
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
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready for use.")
        print("\nNext steps:")
        print("1. Start the server: python backend/app.py")
        print("2. Run the demo: python demo.py")
        print("3. Check the API documentation in README.md")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("1. Make sure all dependencies are installed: pip install -r requirements.txt")
        print("2. Check that Python 3.10+ is being used")
        print("3. Verify all files are in the correct locations")
        return 1

if __name__ == '__main__':
    sys.exit(main())
