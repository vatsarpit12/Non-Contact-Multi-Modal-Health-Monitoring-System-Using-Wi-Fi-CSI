#!/usr/bin/env python3
"""
Demo script showing the health monitoring system in action
"""
import os
import sys
import json
import time
import requests
import numpy as np

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def generate_demo_data():
    """Generate demo CSI data"""
    print("Generating demo CSI data...")
    
    # Generate synthetic CSI data (real-valued for JSON compatibility)
    csi_data = np.random.randn(1000, 3)
    
    # Add some structure
    t = np.linspace(0, 10, 1000)
    
    # Add respiratory component
    resp_freq = 0.3  # 18 breaths per minute
    resp_amp = 0.3
    csi_data += resp_amp * np.sin(2 * np.pi * resp_freq * t)[:, np.newaxis]
    
    # Add cardiac component
    cardiac_freq = 1.5  # 90 bpm
    cardiac_amp = 0.15
    csi_data += cardiac_amp * np.sin(2 * np.pi * cardiac_freq * t)[:, np.newaxis]
    
    # Add noise
    noise_level = 0.05
    csi_data += noise_level * np.random.randn(1000, 3)
    
    # Ensure all values are real and JSON serializable
    csi_data = np.real(csi_data)  # Remove any imaginary parts
    csi_data = csi_data.astype(float)  # Ensure float type
    
    return csi_data.tolist()

def test_api():
    """Test the API endpoints"""
    base_url = "http://localhost:5001"
    headers = {"Authorization": "Bearer dev-token-123"}
    
    print("Testing API endpoints...")
    
    # Test health check
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{base_url}/api/v1/health")
        print(f"   Health check: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        elif response.status_code == 500:
            print("   Health check returned 500 (expected due to missing models)")
        else:
            print(f"   Unexpected status code: {response.status_code}")
    except Exception as e:
        print(f"   Health check failed: {e}")
        return False
    
    # Test patient creation
    print("\n2. Creating test patient...")
    try:
        patient_data = {
            "name": "Demo Patient",
            "age": 65,
            "conditions": "Hypertension;Diabetes"
        }
        response = requests.post(f"{base_url}/api/v1/patients", 
                               json=patient_data, 
                               headers=headers)
        print(f"   Patient creation: {response.status_code}")
        if response.status_code == 201:
            patient = response.json()
            patient_id = patient['id']
            print(f"   Patient ID: {patient_id}")
        else:
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"   Patient creation failed: {e}")
        return False
    
    # Test recording upload
    print("\n3. Uploading recording...")
    try:
        # Generate demo data
        csi_data = generate_demo_data()
        
        # Save to temporary file
        temp_file = "temp_recording.json"
        with open(temp_file, 'w') as f:
            json.dump({"csi_data": csi_data}, f)
        
        # Upload recording
        with open(temp_file, 'rb') as f:
            files = {'file': (temp_file, f, 'application/json')}
            data = {
                'patient_id': patient_id,
                'device_id': 'demo_device'
            }
            response = requests.post(f"{base_url}/api/v1/recordings", 
                                   files=files, 
                                   data=data, 
                                   headers=headers)
        
        print(f"   Recording upload: {response.status_code}")
        if response.status_code == 201:
            recording = response.json()
            recording_id = recording['id']
            print(f"   Recording ID: {recording_id}")
        else:
            print(f"   Error: {response.text}")
            return False
        
        # Clean up temp file
        os.unlink(temp_file)
        
    except Exception as e:
        print(f"   Recording upload failed: {e}")
        return False
    
    # Test recording processing
    print("\n4. Processing recording...")
    try:
        response = requests.post(f"{base_url}/api/v1/recordings/{recording_id}/process", 
                               headers=headers)
        print(f"   Recording processing: {response.status_code}")
        if response.status_code == 200:
            metrics = response.json()
            print(f"   Metrics: {metrics}")
        else:
            print(f"   Error: {response.text}")
            # This might fail due to missing ML models, which is expected
    except Exception as e:
        print(f"   Recording processing failed: {e}")
        # This might fail due to missing ML models, which is expected
    
    # Test getting patient info
    print("\n5. Getting patient information...")
    try:
        response = requests.get(f"{base_url}/api/v1/patients/{patient_id}", 
                              headers=headers)
        print(f"   Patient info: {response.status_code}")
        if response.status_code == 200:
            patient_info = response.json()
            print(f"   Patient: {patient_info['name']}, Age: {patient_info['age']}")
    except Exception as e:
        print(f"   Patient info failed: {e}")
    
    print("\n✓ API demo completed!")
    return True

def main():
    """Main demo function"""
    print("Health Monitoring System Demo")
    print("=" * 40)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:5001/api/v1/health", timeout=5)
        print("✓ Server is running")
    except Exception as e:
        print("✗ Server is not running. Please start the server first:")
        print("  python backend/app.py")
        print("  or")
        print("  ./scripts/run_server.sh")
        return 1
    
    # Run API tests
    if test_api():
        print("\n✓ Demo completed successfully!")
        return 0
    else:
        print("\n✗ Demo failed. Please check the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
