# Health Monitoring System - Frontend

A modern web interface for the Non-Contact Multi-Modal Health Monitoring System using Wi-Fi CSI.

## Features

- 🏠 **Dashboard**: Overview of system status and quick actions
- 👥 **Patient Management**: Add, view, and manage patient information
- 📊 **Health Monitoring**: View recordings and health metrics
- 📤 **Data Upload**: Upload CSI recordings for analysis
- 🎮 **Interactive Demo**: Run the complete system demo
- 💓 **Health Status**: Monitor system health and API status

## Quick Start

### Prerequisites

1. **Backend Server**: Ensure the backend API is running on port 5001
   ```bash
   cd ..
   python -m backend.app
   ```

2. **Python Dependencies**: Install required packages
   ```bash
   pip install -r requirements.txt
   ```

### Running the Frontend

#### Option 1: Using the startup script (Recommended)
```bash
python run_frontend.py
```

#### Option 2: Direct execution
```bash
python app.py
```

The frontend will be available at: **http://localhost:5002**

## Usage

### 1. Home Dashboard
- View system overview and features
- Quick access to all major functions
- System status indicators

### 2. Patient Management
- **Add Patients**: Create new patient records with medical conditions
- **View Patients**: Browse all patients in the system
- **Patient Details**: View individual patient information and health data

### 3. Data Upload
- **Select Patient**: Choose from existing patients
- **Upload File**: Upload JSON or CSV CSI recordings
- **Automatic Processing**: System processes recordings and extracts health metrics

### 4. Health Monitoring
- **View Recordings**: See all uploaded recordings
- **Health Metrics**: Display extracted vital signs and risk scores
- **Status Tracking**: Monitor processing status

### 5. Interactive Demo
- **Run Complete Demo**: Test the entire system workflow
- **Real-time Output**: See demo progress and results
- **Sample Metrics**: View generated health data

### 6. System Health
- **API Status**: Check backend connectivity
- **Database Status**: Verify database connection
- **Model Status**: Check ML model availability

## File Structure

```
frontend/
├── app.py                 # Main Flask application
├── run_frontend.py        # Startup script
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── index.html        # Home page
│   ├── patients.html     # Patients list
│   ├── new_patient.html  # Add patient form
│   ├── patient_detail.html # Patient details
│   ├── recordings.html   # Recordings list
│   ├── upload.html       # Upload form
│   ├── demo.html         # Demo page
│   └── health.html       # System health
├── static/               # Static assets
│   ├── css/
│   │   └── style.css     # Custom styles
│   └── js/
│       └── main.js       # JavaScript functionality
└── uploads/              # Upload directory (auto-created)
```

## API Integration

The frontend integrates with the backend API endpoints:

- `GET /api/v1/health` - System health check
- `GET /api/v1/patients` - List patients
- `POST /api/v1/patients` - Create patient
- `GET /api/v1/patients/{id}` - Get patient details
- `POST /api/v1/recordings` - Upload recording
- `POST /api/v1/recordings/{id}/process` - Process recording

## Configuration

### Environment Variables
- `API_BASE_URL`: Backend API URL (default: http://localhost:5001/api/v1)
- `UPLOAD_FOLDER`: Directory for file uploads (default: ./uploads)

### Port Configuration
- Default port: 5002
- Change in `app.py` if needed

## Troubleshooting

### Common Issues

1. **Port 5000 in use**: The system automatically uses port 5002
2. **Backend not running**: Ensure backend is running on port 5001
3. **Upload errors**: Check file format (JSON/CSV) and permissions
4. **API errors**: Verify backend API is accessible

### Debug Mode
The frontend runs in debug mode by default, providing detailed error messages and auto-reload on changes.

## Development

### Adding New Features
1. Add routes in `app.py`
2. Create templates in `templates/`
3. Add styles in `static/css/style.css`
4. Add JavaScript in `static/js/main.js`

### Template Structure
- All templates extend `base.html`
- Use Bootstrap 5 for styling
- Include Font Awesome icons
- Follow responsive design principles

## Security Notes

- This is a development version
- Change the secret key in production
- Implement proper authentication
- Validate all file uploads
- Use HTTPS in production

## Support

For issues or questions:
1. Check the backend API status
2. Verify all dependencies are installed
3. Check the console for error messages
4. Ensure proper file permissions
