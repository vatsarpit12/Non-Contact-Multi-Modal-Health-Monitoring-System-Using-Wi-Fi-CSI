#!/usr/bin/env python3
"""
Flask frontend application for Health Monitoring System
"""
import os
import sys
import json
import requests
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.utils import secure_filename

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-in-production'

# Configuration
API_BASE_URL = "http://localhost:5001/api/v1"
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'json', 'csv'}

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def make_api_request(method, endpoint, data=None, files=None):
    """Make API request to backend"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        headers = {"Authorization": "Bearer dev-token-123"}
        
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers)
        elif method.upper() == 'POST':
            if files:
                response = requests.post(url, data=data, files=files, headers=headers)
            else:
                response = requests.post(url, json=data, headers=headers)
        elif method.upper() == 'PUT':
            response = requests.put(url, json=data, headers=headers)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            return None, "Invalid method"
        
        return response, None
    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to backend API. Please ensure the backend server is running."
    except Exception as e:
        return None, str(e)

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/patients')
def patients():
    """Patients list page"""
    response, error = make_api_request('GET', '/patients')
    if error:
        flash(f"Error loading patients: {error}", 'error')
        return render_template('patients.html', patients=[])
    
    if response.status_code == 200:
        patients_data = response.json()
        return render_template('patients.html', patients=patients_data)
    else:
        flash(f"Error loading patients: {response.text}", 'error')
        return render_template('patients.html', patients=[])

@app.route('/patients/new', methods=['GET', 'POST'])
def new_patient():
    """Create new patient"""
    if request.method == 'POST':
        patient_data = {
            'name': request.form['name'],
            'age': int(request.form['age']),
            'conditions': request.form.get('conditions', '')
        }
        
        response, error = make_api_request('POST', '/patients', patient_data)
        if error:
            flash(f"Error creating patient: {error}", 'error')
            return render_template('new_patient.html')
        
        if response.status_code == 201:
            flash('Patient created successfully!', 'success')
            return redirect(url_for('patients'))
        else:
            flash(f"Error creating patient: {response.text}", 'error')
    
    return render_template('new_patient.html')

@app.route('/patients/<int:patient_id>')
def patient_detail(patient_id):
    """Patient detail page"""
    response, error = make_api_request('GET', f'/patients/{patient_id}')
    if error:
        flash(f"Error loading patient: {error}", 'error')
        return redirect(url_for('patients'))
    
    if response.status_code == 200:
        patient = response.json()
        
        # Get recent metrics for this patient
        metrics_response, metrics_error = make_api_request('GET', f'/patients/{patient_id}/metrics')
        recent_metrics = []
        if not metrics_error and metrics_response.status_code == 200:
            metrics_data = metrics_response.json()
            recent_metrics = metrics_data.get('recent_metrics', [])
        
        return render_template('patient_detail.html', patient=patient, recent_metrics=recent_metrics)
    else:
        flash(f"Error loading patient: {response.text}", 'error')
        return redirect(url_for('patients'))

@app.route('/recordings')
def recordings():
    """Recordings list page"""
    # Get all patients first
    patients_response, error = make_api_request('GET', '/patients')
    if error:
        flash(f"Error loading patients: {error}", 'error')
        return render_template('recordings.html', recordings=[], patients=[])
    
    patients_data = patients_response.json() if patients_response.status_code == 200 else []
    
    # Get all recordings
    recordings_response, error = make_api_request('GET', '/recordings')
    if error:
        flash(f"Error loading recordings: {error}", 'error')
        return render_template('recordings.html', recordings=[], patients=patients_data)
    
    recordings_data = recordings_response.json() if recordings_response.status_code == 200 else []
    
    return render_template('recordings.html', recordings=recordings_data, patients=patients_data)

@app.route('/upload', methods=['GET', 'POST'])
def upload_recording():
    """Upload recording page"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return render_template('upload.html')
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return render_template('upload.html')
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Upload to API
            patient_id = int(request.form['patient_id'])
            device_id = request.form.get('device_id', 'web_upload')
            
            print(f"DEBUG: Uploading file {filename} for patient {patient_id} with device {device_id}")
            
            with open(file_path, 'rb') as f:
                files = {'file': (filename, f, 'application/json')}
                data = {
                    'patient_id': patient_id,
                    'device_id': device_id
                }
                
                print(f"DEBUG: Making API request to upload recording")
                response, error = make_api_request('POST', '/recordings', data, files)
                if error:
                    print(f"DEBUG: Upload error: {error}")
                    flash(f"Error uploading recording: {error}", 'error')
                    return render_template('upload.html', patients=patients)
                elif response.status_code == 201:
                    recording = response.json()
                    print(f"DEBUG: Recording uploaded successfully with ID: {recording['id']}")
                    flash(f'Recording uploaded successfully! ID: {recording["id"]}', 'success')
                    
                    # Process the recording
                    print(f"DEBUG: Processing recording {recording['id']}")
                    process_response, process_error = make_api_request('POST', f'/recordings/{recording["id"]}/process')
                    if process_error:
                        print(f"DEBUG: Processing error: {process_error}")
                        flash(f"Error processing recording: {process_error}", 'error')
                        return redirect(url_for('patient_detail', patient_id=patient_id))
                    elif process_response.status_code == 200:
                        metrics = process_response.json()
                        print(f"DEBUG: Recording processed successfully. Metrics: {metrics}")
                        flash(f'Recording processed successfully! Risk Score: {metrics.get("risk_score", "N/A")}', 'success')
                    else:
                        print(f"DEBUG: Processing failed with status {process_response.status_code}: {process_response.text}")
                        flash(f"Error processing recording: {process_response.text}", 'error')
                        return redirect(url_for('patient_detail', patient_id=patient_id))
                else:
                    print(f"DEBUG: Upload failed with status {response.status_code}: {response.text}")
                    flash(f"Error uploading recording: {response.text}", 'error')
                    return render_template('upload.html', patients=patients)
            
            # Clean up uploaded file
            os.remove(file_path)
            return redirect(url_for('patient_detail', patient_id=patient_id))
        else:
            flash('Invalid file type. Please upload JSON or CSV files.', 'error')
    
    # Get patients for dropdown
    response, error = make_api_request('GET', '/patients')
    patients = response.json() if response and response.status_code == 200 else []
    
    return render_template('upload.html', patients=patients)

@app.route('/demo')
def demo():
    """Demo page with sample data"""
    return render_template('demo.html')

@app.route('/api/demo/run', methods=['POST'])
def run_demo():
    """Run the demo programmatically"""
    try:
        import subprocess
        result = subprocess.run([sys.executable, 'demo.py'], 
                              capture_output=True, text=True, cwd='..')
        
        if result.returncode == 0:
            return jsonify({'success': True, 'output': result.stdout})
        else:
            return jsonify({'success': False, 'error': result.stderr})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/health')
def health_status():
    """Health status page"""
    response, error = make_api_request('GET', '/health')
    if error:
        return render_template('health.html', status={'error': error})
    
    if response.status_code == 200:
        status = response.json()
        return render_template('health.html', status=status)
    else:
        return render_template('health.html', status={'error': response.text})

@app.route('/debug-upload')
def debug_upload():
    """Debug upload page"""
    return render_template('debug_upload.html')

@app.route('/recordings/<int:recording_id>/metrics')
def view_recording_metrics(recording_id):
    """View metrics for a specific recording"""
    try:
        # Get the metrics from the backend API
        response, error = make_api_request('GET', f'/recordings/{recording_id}/metrics')
        
        if error:
            flash(f"Error fetching metrics: {error}", 'error')
            return redirect(url_for('recordings'))
        
        if response.status_code == 200:
            metrics_data = response.json()
            return render_template('metrics.html', 
                                 recording_id=recording_id, 
                                 metrics=metrics_data.get('metrics'),
                                 features=metrics_data.get('features'))
        else:
            flash(f"Error fetching metrics: {response.text}", 'error')
            return redirect(url_for('recordings'))
            
    except Exception as e:
        flash(f"Error fetching metrics: {str(e)}", 'error')
        return redirect(url_for('recordings'))

if __name__ == '__main__':
    print("Starting Health Monitoring Frontend...")
    print(f"Upload folder: {UPLOAD_FOLDER}")
    print(f"API Base URL: {API_BASE_URL}")
    app.run(debug=True, port=5002, host='0.0.0.0')
