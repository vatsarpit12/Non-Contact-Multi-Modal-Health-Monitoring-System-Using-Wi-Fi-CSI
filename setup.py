#!/usr/bin/env python3
"""
Setup script for the health monitoring system
"""
import os
import sys
import subprocess
import shutil

def run_command(cmd, cwd=None):
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, 
                              capture_output=True, text=True, timeout=60)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def create_directories():
    """Create necessary directories"""
    print("Creating directories...")
    
    directories = [
        "data/raw",
        "data/synthetic", 
        "models",
        "backend/tests",
        "ml/tests",
        ".github/workflows"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Created {directory}")

def install_dependencies():
    """Install Python dependencies"""
    print("\nInstalling dependencies...")
    
    success, stdout, stderr = run_command("pip install -r requirements.txt")
    if success:
        print("✓ Dependencies installed successfully")
        return True
    else:
        print(f"✗ Failed to install dependencies: {stderr}")
        return False

def generate_synthetic_data():
    """Generate synthetic test data"""
    print("\nGenerating synthetic data...")
    
    success, stdout, stderr = run_command("python scripts/generate_synthetic.py")
    if success:
        print("✓ Synthetic data generated successfully")
        return True
    else:
        print(f"✗ Failed to generate synthetic data: {stderr}")
        return False

def create_database():
    """Create and initialize database"""
    print("\nCreating database...")
    
    success, stdout, stderr = run_command("python scripts/create_db.py")
    if success:
        print("✓ Database created successfully")
        return True
    else:
        print(f"✗ Failed to create database: {stderr}")
        return False

def make_scripts_executable():
    """Make shell scripts executable"""
    print("\nMaking scripts executable...")
    
    scripts = [
        "scripts/run_server.sh",
        "scripts/generate_synthetic.py",
        "scripts/create_db.py",
        "test_setup.py",
        "demo.py",
        "run_tests.py"
    ]
    
    for script in scripts:
        if os.path.exists(script):
            os.chmod(script, 0o755)
            print(f"✓ Made {script} executable")

def run_basic_tests():
    """Run basic tests to verify setup"""
    print("\nRunning basic tests...")
    
    success, stdout, stderr = run_command("python test_setup.py")
    if success:
        print("✓ Basic tests passed")
        return True
    else:
        print(f"✗ Basic tests failed: {stderr}")
        return False

def main():
    """Main setup function"""
    print("Health Monitoring System Setup")
    print("=" * 40)
    
    # Check Python version
    if sys.version_info < (3, 10):
        print("❌ Python 3.10+ is required. Current version:", sys.version)
        return 1
    
    print(f"✓ Python version: {sys.version}")
    
    # Setup steps
    steps = [
        ("Creating directories", create_directories),
        ("Installing dependencies", install_dependencies),
        ("Generating synthetic data", generate_synthetic_data),
        ("Creating database", create_database),
        ("Making scripts executable", make_scripts_executable),
        ("Running basic tests", run_basic_tests)
    ]
    
    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        if not step_func():
            print(f"❌ Setup failed at: {step_name}")
            return 1
    
    print("\n" + "=" * 40)
    print("🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Start the server: python backend/app.py")
    print("2. Run the demo: python demo.py")
    print("3. Run comprehensive tests: python run_tests.py")
    print("4. Check the API documentation in README.md")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
