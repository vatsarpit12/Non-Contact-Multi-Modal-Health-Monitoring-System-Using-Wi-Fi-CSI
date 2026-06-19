"""
Feature extraction utilities for CSI data
"""
import numpy as np
from scipy import signal
from scipy.stats import skew, kurtosis
from sklearn.decomposition import PCA
from .denoise import denoise_csi_data
from .phase_calib import calibrate_phase, extract_amplitude_phase, unwrap_phase, normalize_amplitude

def extract_spectral_features(csi_data, sampling_rate=1000):
    """Extract spectral features from CSI data"""
    features = {}
    
    # Apply FFT
    fft_data = np.fft.fft(csi_data, axis=0)
    freqs = np.fft.fftfreq(len(csi_data), 1/sampling_rate)
    
    # Power spectral density
    psd = np.abs(fft_data) ** 2
    
    # Spectral features
    features['spectral_centroid'] = np.sum(freqs[:, np.newaxis] * psd, axis=0) / np.sum(psd, axis=0)
    features['spectral_bandwidth'] = np.sqrt(np.sum(((freqs[:, np.newaxis] - features['spectral_centroid']) ** 2) * psd, axis=0) / np.sum(psd, axis=0))
    features['spectral_rolloff'] = np.percentile(psd, 85, axis=0)
    features['spectral_flux'] = np.sum(np.diff(psd, axis=0) ** 2, axis=0)
    
    return features

def extract_statistical_features(csi_data):
    """Extract statistical features from CSI data"""
    features = {}
    
    # Basic statistics
    features['mean'] = np.mean(csi_data, axis=0)
    features['std'] = np.std(csi_data, axis=0)
    features['var'] = np.var(csi_data, axis=0)
    features['skewness'] = skew(csi_data, axis=0)
    features['kurtosis'] = kurtosis(csi_data, axis=0)
    
    # Range and percentiles
    features['min'] = np.min(csi_data, axis=0)
    features['max'] = np.max(csi_data, axis=0)
    features['range'] = features['max'] - features['min']
    features['q25'] = np.percentile(csi_data, 25, axis=0)
    features['q75'] = np.percentile(csi_data, 75, axis=0)
    features['iqr'] = features['q75'] - features['q25']
    
    return features

def extract_respiratory_features(csi_data, sampling_rate=1000):
    """Extract respiratory-related features"""
    features = {}
    
    # Bandpass filter for respiratory range (0.1-0.5 Hz)
    nyquist = sampling_rate / 2
    low = max(0.01, 0.1 / nyquist)  # Ensure valid range
    high = min(0.99, 0.5 / nyquist)
    
    if low >= high:
        low = 0.01
        high = 0.99
    
    try:
        b, a = signal.butter(2, [low, high], btype='band')  # Reduced order
        
        # Apply filter to each antenna
        respiratory_data = np.zeros_like(csi_data)
        for i in range(csi_data.shape[1]):
            respiratory_data[:, i] = signal.filtfilt(b, a, csi_data[:, i])
        
        # Extract features
        features['respiratory_amplitude'] = np.std(respiratory_data, axis=0)
        features['respiratory_frequency'] = np.argmax(np.abs(np.fft.fft(respiratory_data, axis=0)), axis=0) * sampling_rate / len(csi_data)
        features['respiratory_energy'] = np.sum(respiratory_data ** 2, axis=0)
    except:
        # Fallback to simple features if filtering fails
        features['respiratory_amplitude'] = np.std(csi_data, axis=0)
        features['respiratory_frequency'] = np.zeros(csi_data.shape[1])
        features['respiratory_energy'] = np.sum(csi_data ** 2, axis=0)
    
    return features

def extract_cardiac_features(csi_data, sampling_rate=1000):
    """Extract cardiac-related features"""
    features = {}
    
    # Bandpass filter for cardiac range (0.5-3 Hz)
    nyquist = sampling_rate / 2
    low = max(0.01, 0.5 / nyquist)  # Ensure valid range
    high = min(0.99, 3.0 / nyquist)
    
    if low >= high:
        low = 0.01
        high = 0.99
    
    try:
        b, a = signal.butter(2, [low, high], btype='band')  # Reduced order
        
        # Apply filter to each antenna
        cardiac_data = np.zeros_like(csi_data)
        for i in range(csi_data.shape[1]):
            cardiac_data[:, i] = signal.filtfilt(b, a, csi_data[:, i])
        
        # Extract features
        features['cardiac_amplitude'] = np.std(cardiac_data, axis=0)
        features['cardiac_frequency'] = np.argmax(np.abs(np.fft.fft(cardiac_data, axis=0)), axis=0) * sampling_rate / len(csi_data)
        features['cardiac_energy'] = np.sum(cardiac_data ** 2, axis=0)
        
        # Heart rate variability (simplified)
        peaks, _ = signal.find_peaks(cardiac_data[:, 0], distance=sampling_rate//3)
        if len(peaks) > 1:
            rr_intervals = np.diff(peaks) / sampling_rate
            features['hrv_rmssd'] = np.sqrt(np.mean(np.diff(rr_intervals) ** 2))
            features['hrv_std'] = np.std(rr_intervals)
        else:
            features['hrv_rmssd'] = 0
            features['hrv_std'] = 0
    except:
        # Fallback to simple features if filtering fails
        features['cardiac_amplitude'] = np.std(csi_data, axis=0)
        features['cardiac_frequency'] = np.zeros(csi_data.shape[1])
        features['cardiac_energy'] = np.sum(csi_data ** 2, axis=0)
        features['hrv_rmssd'] = 0
        features['hrv_std'] = 0
    
    return features

def extract_mobility_features(csi_data, sampling_rate=1000):
    """Extract mobility and activity features"""
    features = {}
    
    # Calculate signal variance (indicator of movement)
    features['signal_variance'] = np.var(csi_data, axis=0)
    
    # Calculate signal energy
    features['signal_energy'] = np.sum(csi_data ** 2, axis=0)
    
    # Calculate zero crossing rate
    features['zero_crossing_rate'] = np.sum(np.diff(np.sign(csi_data), axis=0) != 0, axis=0) / len(csi_data)
    
    # Calculate signal magnitude area
    features['sma'] = np.sum(np.abs(csi_data), axis=0)
    
    # Calculate signal vector magnitude
    features['svm'] = np.sqrt(np.sum(csi_data ** 2, axis=0))
    
    return features

def extract_features(csi_data, sampling_rate=1000):
    """Main feature extraction pipeline"""
    # Convert to numpy array if needed
    if not isinstance(csi_data, np.ndarray):
        csi_data = np.array(csi_data)
    
    # Handle complex data - convert to real for basic feature extraction
    if np.iscomplexobj(csi_data):
        # Use magnitude for feature extraction
        csi_data = np.abs(csi_data)
    
    # Ensure 2D array
    if csi_data.ndim == 1:
        csi_data = csi_data.reshape(-1, 1)
    
    # Denoise data
    csi_data = denoise_csi_data(csi_data, sampling_rate)
    
    # For real data, skip phase calibration
    # csi_data = calibrate_phase(csi_data)
    
    # For real data, use the data directly as amplitude
    amplitude = csi_data
    # phase = np.zeros_like(csi_data)  # No phase for real data
    
    # Normalize amplitude
    amplitude = normalize_amplitude(amplitude)
    
    # Extract features
    features = {}
    
    # Spectral features
    spectral_features = extract_spectral_features(csi_data, sampling_rate)
    features.update(spectral_features)
    
    # Statistical features
    statistical_features = extract_statistical_features(csi_data)
    features.update(statistical_features)
    
    # Respiratory features
    respiratory_features = extract_respiratory_features(csi_data, sampling_rate)
    features.update(respiratory_features)
    
    # Cardiac features
    cardiac_features = extract_cardiac_features(csi_data, sampling_rate)
    features.update(cardiac_features)
    
    # Mobility features
    mobility_features = extract_mobility_features(csi_data, sampling_rate)
    features.update(mobility_features)
    
    # Convert numpy arrays to lists for JSON serialization
    for key, value in features.items():
        if isinstance(value, np.ndarray):
            features[key] = value.tolist()
        elif isinstance(value, np.floating):
            features[key] = float(value)
        elif isinstance(value, np.integer):
            features[key] = int(value)
    
    return features
