"""
Denoising utilities for CSI data
"""
import numpy as np
from scipy import signal
from scipy.ndimage import median_filter

def apply_median_filter(data, kernel_size=3):
    """Apply median filter to remove outliers"""
    return median_filter(data, size=kernel_size)

def apply_butterworth_filter(data, cutoff_freq, sampling_rate, order=4):
    """Apply Butterworth low-pass filter"""
    nyquist = sampling_rate / 2
    normal_cutoff = cutoff_freq / nyquist
    
    # Ensure cutoff is valid
    if normal_cutoff >= 1.0:
        normal_cutoff = 0.99
    if normal_cutoff <= 0.0:
        normal_cutoff = 0.01
    
    # Reduce order if data is too short
    if len(data) < 2 * order + 1:
        order = max(1, len(data) // 2 - 1)
    
    b, a = signal.butter(order, normal_cutoff, btype='low', analog=False)
    return signal.filtfilt(b, a, data)

def remove_dc_component(data):
    """Remove DC component from signal"""
    return data - np.mean(data)

def apply_savgol_filter(data, window_length=11, polyorder=3):
    """Apply Savitzky-Golay filter for smoothing"""
    # Ensure window_length is odd and less than data length
    if window_length % 2 == 0:
        window_length += 1
    if window_length >= len(data):
        window_length = min(11, len(data) - 1)
        if window_length % 2 == 0:
            window_length -= 1
    
    # Ensure polyorder is less than window_length
    if polyorder >= window_length:
        polyorder = max(1, window_length - 1)
    
    return signal.savgol_filter(data, window_length, polyorder)

def denoise_csi_data(csi_data, sampling_rate=1000):
    """Main denoising pipeline for CSI data"""
    # Convert to numpy array if needed
    if not isinstance(csi_data, np.ndarray):
        csi_data = np.array(csi_data)
    
    # Remove DC component
    csi_data = remove_dc_component(csi_data)
    
    # Apply median filter to remove outliers (only if data is long enough)
    if len(csi_data) > 3:
        csi_data = apply_median_filter(csi_data)
    
    # Skip complex filtering for short data
    if len(csi_data) > 50:
        try:
            # Apply Butterworth filter for noise reduction
            csi_data = apply_butterworth_filter(csi_data, cutoff_freq=50, sampling_rate=sampling_rate)
        except:
            pass  # Skip if filtering fails
        
        try:
            # Apply Savitzky-Golay filter for smoothing
            csi_data = apply_savgol_filter(csi_data)
        except:
            pass  # Skip if filtering fails
    
    return csi_data
