"""
Phase calibration utilities for CSI data
"""
import numpy as np
from scipy import signal
from sklearn.decomposition import PCA

def calibrate_phase(csi_data, reference_antenna=0):
    """Calibrate phase using reference antenna"""
    if csi_data.shape[1] <= reference_antenna:
        return csi_data
    
    # Use first antenna as reference
    ref_phase = np.angle(csi_data[:, reference_antenna])
    
    # Calibrate other antennas
    calibrated_data = csi_data.copy()
    for i in range(csi_data.shape[1]):
        if i != reference_antenna:
            phase_diff = np.angle(csi_data[:, i]) - ref_phase
            calibrated_data[:, i] = np.abs(csi_data[:, i]) * np.exp(1j * (ref_phase + phase_diff))
    
    return calibrated_data

def apply_pca_denoising(csi_data, n_components=0.95):
    """Apply PCA for denoising and dimensionality reduction"""
    # Reshape data for PCA
    original_shape = csi_data.shape
    data_reshaped = csi_data.reshape(original_shape[0], -1)
    
    # Apply PCA
    pca = PCA(n_components=n_components)
    data_pca = pca.fit_transform(data_reshaped)
    
    # Reconstruct data
    data_reconstructed = pca.inverse_transform(data_pca)
    
    # Reshape back to original shape
    return data_reconstructed.reshape(original_shape)

def extract_amplitude_phase(csi_data):
    """Extract amplitude and phase from complex CSI data"""
    amplitude = np.abs(csi_data)
    phase = np.angle(csi_data)
    
    return amplitude, phase

def unwrap_phase(phase):
    """Unwrap phase to remove discontinuities"""
    return np.unwrap(phase)

def normalize_amplitude(amplitude):
    """Normalize amplitude to [0, 1] range"""
    return (amplitude - np.min(amplitude)) / (np.max(amplitude) - np.min(amplitude) + 1e-8)
