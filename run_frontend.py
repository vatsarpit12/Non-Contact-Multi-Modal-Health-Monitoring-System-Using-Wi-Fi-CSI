#!/usr/bin/env python3
"""
Startup script for the Flask frontend
"""
import os
import sys
import subprocess

def check_backend():
    """Check if backend is running"""
    try:
        import requests
        response = requests.get("http://localhost:5001/api/v1/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    print("Health Monitoring System - Frontend")
    print("=" * 40)
    
    # Check if backend is running
    if not check_backend():
        print("❌ Backend server is not running!")
        print("Please start the backend server first:")
        print("  cd .. && python -m backend.app")
        print("  or")
        print("  cd .. && ./scripts/run_server.sh")
        return 1
    
    print("✅ Backend server is running")
    print("🚀 Starting frontend server...")
    print("📱 Frontend will be available at: http://localhost:5002")
    print("🔧 Backend API is available at: http://localhost:5001")
    print("\nPress Ctrl+C to stop the server")
    print("-" * 40)
    
    # Start the frontend
    try:
        from app import app
        app.run(debug=True, port=5002, host='0.0.0.0')
    except KeyboardInterrupt:
        print("\n👋 Frontend server stopped")
        return 0
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
