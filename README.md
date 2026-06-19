# Non-Contact Multi-Modal Health Monitoring using Wi-Fi CSI

A Flask-based backend system for health monitoring using Wi-Fi Channel State Information (CSI) data. This system provides REST APIs for ingesting CSI data, processing it through machine learning models, and generating health alerts.

## Features

- **REST API**: Complete Flask-based API for patient management, data ingestion, and health monitoring
- **Machine Learning**: CNN, LSTM, and TCN models for respiration, cardiac, and mobility analysis
- **Database**: SQLite database for storing patients, recordings, features, and alerts
- **Risk Scoring**: Automated risk assessment and alert generation
- **Testing**: Comprehensive unit and integration tests
- **CI/CD**: GitHub Actions workflow for automated testing

## Project Structure

```
project-root/
├── backend/                      # Flask application
│   ├── app.py                   # Main Flask app
│   ├── config.py                # Configuration settings
│   ├── models.py                # Database models
│   ├── routes/                  # API route blueprints
│   │   ├── ingest.py           # Data ingestion routes
│   │   ├── patients.py         # Patient management routes
│   │   ├── inference.py        # ML inference routes
│   │   └── health.py           # Health monitoring routes
│   └── tests/                   # Backend tests
├── data/
│   ├── synthetic/               # Synthetic test data
│   └── raw/                     # Raw CSI recordings
├── ml/
│   ├── train.py                 # Model training script
│   ├── inference.py             # Inference pipeline
│   ├── models.py                # ML model definitions
│   └── tests/                   # ML tests
├── preprocess/
│   ├── denoise.py               # Denoising utilities
│   ├── phase_calib.py           # Phase calibration
│   └── features.py              # Feature extraction
├── scripts/
│   ├── run_server.sh            # Server startup script
│   ├── create_db.py             # Database initialization
│   └── generate_synthetic.py    # Synthetic data generation
├── requirements.txt             # Python dependencies
└── .github/workflows/ci.yml     # CI configuration
```

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Non-Contact-Multi-Modal-Health-Monitoring-using-Wi-Fi-CSI
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   export FLASK_ENV=development
   export DEV_API_TOKEN=dev-token-123
   export DATABASE_URL=sqlite:///app.db
   export MODEL_DIR=./models
   ```

4. **Create necessary directories**
   ```bash
   mkdir -p data/raw data/synthetic models
   ```

5. **Initialize database**
   ```bash
   python scripts/create_db.py
   ```

6. **Generate synthetic data**
   ```bash
   python scripts/generate_synthetic.py
   ```

## Usage

### Starting the Server

```bash
# Using the provided script
./scripts/run_server.sh

# Or directly with Python
python backend/app.py
```

The server will start on `http://localhost:5000`

### API Endpoints

#### Authentication
All API endpoints require authentication using a Bearer token:
```bash
Authorization: Bearer dev-token-123
```

#### Patient Management

**Create Patient**
```bash
curl -X POST http://localhost:5000/api/v1/patients \
  -H "Authorization: Bearer dev-token-123" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Subject","age":72,"conditions":"COPD;Hypertension"}'
```

**Get Patient**
```bash
curl -X GET http://localhost:5000/api/v1/patients/1 \
  -H "Authorization: Bearer dev-token-123"
```

**Get Patient Alerts**
```bash
curl -X GET http://localhost:5000/api/v1/patients/1/alerts \
  -H "Authorization: Bearer dev-token-123"
```

#### Data Ingestion

**Upload Recording**
```bash
curl -X POST http://localhost:5000/api/v1/recordings \
  -H "Authorization: Bearer dev-token-123" \
  -F "patient_id=1" \
  -F "device_id=wifi_nexmon" \
  -F "file=@data/synthetic/synthetic_000.json"
```

**Process Recording**
```bash
curl -X POST http://localhost:5000/api/v1/recordings/1/process \
  -H "Authorization: Bearer dev-token-123"
```

**Get Recording Metrics**
```bash
curl -X GET http://localhost:5000/api/v1/recordings/1/metrics \
  -H "Authorization: Bearer dev-token-123"
```

#### Model Training

**Start Training**
```bash
curl -X POST http://localhost:5000/api/v1/models/train \
  -H "Authorization: Bearer dev-token-123" \
  -H "Content-Type: application/json" \
  -d '{"model_type":"respiration","params":{}}'
```

**Get Training Status**
```bash
curl -X GET http://localhost:5000/api/v1/models/1/status \
  -H "Authorization: Bearer dev-token-123"
```

#### Health Check

**Health Check**
```bash
curl -X GET http://localhost:5000/api/v1/health
```

## Database Schema

### Tables

- **patients**: Patient information and metadata
- **recordings**: CSI data recordings with file paths
- **features**: Extracted features from CSI data
- **metrics**: Health metrics (respiration rate, heart rate, HRV, activity)
- **alerts**: Health alerts and warnings
- **model_runs**: ML model training runs and artifacts

### Key Fields

- `patients`: id, name, age, conditions, created_at
- `recordings`: id, patient_id, path, device_id, timestamp, processed
- `features`: id, recording_id, feature_json, created_at
- `metrics`: id, recording_id, respiration_rate, heart_rate, hrv, activity_label, risk_score
- `alerts`: id, patient_id, metric_id, level, message, created_at

## Machine Learning Models

### Model Types

1. **Respiration CNN**: Estimates respiration rate from CSI data
2. **Cardiac LSTM**: Predicts heart rate and HRV
3. **Mobility TCN**: Classifies activity and detects falls

### Training

```bash
# Train all models
python ml/train.py

# Train specific model
python -c "from ml.train import train_model; train_model('respiration')"
```

### Model Artifacts

Trained models are saved in the `models/` directory:
- `respiration_model.pth`: Respiration rate estimation model
- `cardiac_model.pth`: Cardiac metrics model
- `mobility_model.pth`: Activity classification model
- `*_scaler.pkl`: Feature normalization scalers

## Testing

### Run Tests

```bash
# Run all tests
pytest

# Run specific test modules
pytest backend/tests/
pytest ml/tests/

# Run with coverage
pytest --cov=backend --cov=ml
```

### Test Coverage

The test suite includes:
- Unit tests for all API endpoints
- ML model architecture tests
- Database model tests
- Feature extraction tests
- Integration tests for the full pipeline

## Risk Scoring

The system calculates risk scores based on:

- **Respiration**: Deviation from normal range (12-20 breaths/min)
- **Cardiac**: Heart rate and HRV abnormalities
- **Mobility**: Activity patterns and fall detection

Risk levels:
- **Low**: 30-60
- **Medium**: 60-80
- **High**: 80-100

## Configuration

### Environment Variables

- `FLASK_ENV`: Flask environment (development/production)
- `DEV_API_TOKEN`: API authentication token
- `DATABASE_URL`: Database connection string
- `MODEL_DIR`: Directory for ML model artifacts
- `UPLOAD_FOLDER`: Directory for uploaded files
- `LOG_LEVEL`: Logging level (DEBUG/INFO/WARNING/ERROR)

### Risk Scoring Weights

Configurable in `backend/config.py`:
```python
RISK_WEIGHTS = {
    'respiration': 0.4,
    'cardiac': 0.4,
    'mobility': 0.2
}
```

## Development

### Adding New Features

1. Create new route blueprints in `backend/routes/`
2. Add corresponding database models in `backend/models.py`
3. Write tests in `backend/tests/`
4. Update API documentation in README

### Adding New ML Models

1. Define model architecture in `ml/models.py`
2. Add training logic in `ml/train.py`
3. Update inference pipeline in `ml/inference.py`
4. Add tests in `ml/tests/`

## Troubleshooting

### Common Issues

1. **Database errors**: Ensure database is initialized with `python scripts/create_db.py`
2. **Model loading errors**: Train models first with `python ml/train.py`
3. **File upload errors**: Check `UPLOAD_FOLDER` permissions
4. **Authentication errors**: Verify `DEV_API_TOKEN` is set correctly

### Logs

Check application logs for detailed error information:
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python backend/app.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Wi-Fi CSI research community
- Flask and PyTorch communities
- Health monitoring research teams
