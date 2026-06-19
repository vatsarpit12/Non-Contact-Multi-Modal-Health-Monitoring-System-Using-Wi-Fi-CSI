"""
Training script for health monitoring models
"""
import os
import json
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, accuracy_score
import logging

from .models import create_models
from preprocess.features import extract_features

# Set random seeds for reproducibility
torch.manual_seed(42)
np.random.seed(42)

logger = logging.getLogger(__name__)

def load_synthetic_data(data_dir='data/synthetic'):
    """Load synthetic CSI data for training"""
    # Generate synthetic data if it doesn't exist
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        generate_synthetic_data(data_dir)
    
    # Load synthetic data
    data_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
    if not data_files:
        generate_synthetic_data(data_dir)
        data_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
    
    all_data = []
    all_labels = []
    
    for file in data_files:
        with open(os.path.join(data_dir, file), 'r') as f:
            data = json.load(f)
            all_data.append(data['csi_data'])
            all_labels.append(data['labels'])
    
    return np.array(all_data), np.array(all_labels)

def generate_synthetic_data(data_dir, num_samples=100):
    """Generate synthetic CSI data for training and testing"""
    os.makedirs(data_dir, exist_ok=True)
    
    for i in range(num_samples):
        # Generate synthetic CSI data (simulating 3 antennas, 1000 samples)
        csi_data = np.random.randn(1000, 3) + 1j * np.random.randn(1000, 3)
        
        # Add some structure to make it more realistic
        t = np.linspace(0, 10, 1000)
        
        # Add respiratory component
        resp_freq = np.random.uniform(0.2, 0.4)  # 12-24 breaths per minute
        resp_amp = np.random.uniform(0.1, 0.5)
        csi_data += resp_amp * np.exp(1j * 2 * np.pi * resp_freq * t)[:, np.newaxis]
        
        # Add cardiac component
        cardiac_freq = np.random.uniform(1.0, 2.0)  # 60-120 bpm
        cardiac_amp = np.random.uniform(0.05, 0.2)
        csi_data += cardiac_amp * np.exp(1j * 2 * np.pi * cardiac_freq * t)[:, np.newaxis]
        
        # Add noise
        noise_level = np.random.uniform(0.01, 0.1)
        csi_data += noise_level * (np.random.randn(1000, 3) + 1j * np.random.randn(1000, 3))
        
        # Generate labels
        labels = {
            'respiration_rate': resp_freq * 60,  # Convert to breaths per minute
            'heart_rate': cardiac_freq * 60,     # Convert to beats per minute
            'hrv': np.random.uniform(20, 50),    # Random HRV
            'activity_label': np.random.choice(['normal', 'walking', 'sitting', 'standing', 'fall'])
        }
        
        # Save data
        data = {
            'csi_data': csi_data.tolist(),
            'labels': labels
        }
        
        with open(os.path.join(data_dir, f'synthetic_{i:03d}.json'), 'w') as f:
            json.dump(data, f)

def prepare_data(data, labels, test_size=0.2):
    """Prepare data for training"""
    # Extract features
    features = []
    respiration_labels = []
    cardiac_labels = []
    mobility_labels = []
    
    for i, (csi_data, label) in enumerate(zip(data, labels)):
        try:
            # Extract features
            feature_dict = extract_features(csi_data)
            
            # Convert features to array
            feature_array = []
            for key, value in feature_dict.items():
                if isinstance(value, list):
                    feature_array.extend(value)
                else:
                    feature_array.append(value)
            
            # Check for NaN or Inf in feature array
            feature_array = np.array(feature_array)
            if np.isnan(feature_array).any() or np.isinf(feature_array).any():
                logger.warning(f"Sample {i} has NaN/Inf features, skipping")
                continue
                
            features.append(feature_array.tolist())
            respiration_labels.append(label['respiration_rate'])
            cardiac_labels.append([label['heart_rate'], label['hrv']])
            mobility_labels.append(label['activity_label'])
            
        except Exception as e:
            logger.warning(f"Failed to extract features for sample {i}: {e}")
            continue
    
    features = np.array(features)
    respiration_labels = np.array(respiration_labels)
    cardiac_labels = np.array(cardiac_labels)
    mobility_labels = np.array(mobility_labels)
    
    logger.info(f"Features shape: {features.shape}")
    logger.info(f"Features contains NaN: {np.isnan(features).any()}")
    logger.info(f"Features contains Inf: {np.isinf(features).any()}")
    
    # Handle NaN values in features
    features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)
    
    # Normalize features
    scaler = StandardScaler()
    features = scaler.fit_transform(features)
    
    # Split data
    X_train, X_test, y_resp_train, y_resp_test, y_card_train, y_card_test, y_mob_train, y_mob_test = train_test_split(
        features, respiration_labels, cardiac_labels, mobility_labels, test_size=test_size, random_state=42
    )
    
    return (X_train, X_test, y_resp_train, y_resp_test, 
            y_card_train, y_card_test, y_mob_train, y_mob_test, scaler)

def train_respiration_model(X_train, y_train, X_test, y_test, device='cpu'):
    """Train respiration rate estimation model"""
    # Create a simple MLP model for feature-based input instead of CNN
    class RespirationMLP(nn.Module):
        def __init__(self, input_size):
            super(RespirationMLP, self).__init__()
            self.fc1 = nn.Linear(input_size, 256)
            self.dropout1 = nn.Dropout(0.5)
            self.fc2 = nn.Linear(256, 128)
            self.dropout2 = nn.Dropout(0.3)
            self.fc3 = nn.Linear(128, 64)
            self.dropout3 = nn.Dropout(0.2)
            self.fc4 = nn.Linear(64, 1)
        
        def forward(self, x):
            x = F.relu(self.fc1(x))
            x = self.dropout1(x)
            x = F.relu(self.fc2(x))
            x = self.dropout2(x)
            x = F.relu(self.fc3(x))
            x = self.dropout3(x)
            x = self.fc4(x)
            return x
    
    model = RespirationMLP(X_train.shape[1]).to(device)
    
    # Prepare data
    X_train_tensor = torch.FloatTensor(X_train)
    y_train_tensor = torch.FloatTensor(y_train).unsqueeze(1)
    X_test_tensor = torch.FloatTensor(X_test)
    y_test_tensor = torch.FloatTensor(y_test).unsqueeze(1)
    
    # Create data loaders
    train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    
    # Training setup
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=10, factor=0.5)
    
    # Training loop
    model.train()
    for epoch in range(100):
        total_loss = 0
        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        
        avg_loss = total_loss / len(train_loader)
        scheduler.step(avg_loss)
        
        if epoch % 20 == 0:
            logger.info(f"Epoch {epoch}, Loss: {avg_loss:.4f}")
    
    # Evaluate
    model.eval()
    with torch.no_grad():
        test_pred = model(X_test_tensor)
        test_mae = mean_absolute_error(y_test, test_pred.numpy())
        test_mse = mean_squared_error(y_test, test_pred.numpy())
    
    logger.info(f"Respiration Model - Test MAE: {test_mae:.4f}, Test MSE: {test_mse:.4f}")
    
    return model, {'mae': test_mae, 'mse': test_mse}

def train_cardiac_model(X_train, y_train, X_test, y_test, device='cpu'):
    """Train cardiac metrics estimation model"""
    # Create a simple MLP model for feature-based input instead of LSTM
    class CardiacMLP(nn.Module):
        def __init__(self, input_size):
            super(CardiacMLP, self).__init__()
            self.fc1 = nn.Linear(input_size, 256)
            self.dropout1 = nn.Dropout(0.5)
            self.fc2 = nn.Linear(256, 128)
            self.dropout2 = nn.Dropout(0.3)
            self.fc3 = nn.Linear(128, 64)
            self.dropout3 = nn.Dropout(0.2)
            self.fc4 = nn.Linear(64, 2)  # Heart rate and HRV
        
        def forward(self, x):
            x = F.relu(self.fc1(x))
            x = self.dropout1(x)
            x = F.relu(self.fc2(x))
            x = self.dropout2(x)
            x = F.relu(self.fc3(x))
            x = self.dropout3(x)
            x = self.fc4(x)
            return x
    
    model = CardiacMLP(X_train.shape[1]).to(device)
    
    # Prepare data
    X_train_tensor = torch.FloatTensor(X_train)
    y_train_tensor = torch.FloatTensor(y_train)
    X_test_tensor = torch.FloatTensor(X_test)
    y_test_tensor = torch.FloatTensor(y_test)
    
    # Create data loaders
    train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    
    # Training setup
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=10, factor=0.5)
    
    # Training loop
    model.train()
    for epoch in range(100):
        total_loss = 0
        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        
        avg_loss = total_loss / len(train_loader)
        scheduler.step(avg_loss)
        
        if epoch % 20 == 0:
            logger.info(f"Epoch {epoch}, Loss: {avg_loss:.4f}")
    
    # Evaluate
    model.eval()
    with torch.no_grad():
        test_pred = model(X_test_tensor)
        test_mae = mean_absolute_error(y_test, test_pred.numpy())
        test_mse = mean_squared_error(y_test, test_pred.numpy())
    
    logger.info(f"Cardiac Model - Test MAE: {test_mae:.4f}, Test MSE: {test_mse:.4f}")
    
    return model, {'mae': test_mae, 'mse': test_mse}

def train_mobility_model(X_train, y_train, X_test, y_test, device='cpu'):
    """Train mobility classification model"""
    # Create a simple MLP model for feature-based input instead of TCN
    class MobilityMLP(nn.Module):
        def __init__(self, input_size, num_classes=5):
            super(MobilityMLP, self).__init__()
            self.fc1 = nn.Linear(input_size, 256)
            self.dropout1 = nn.Dropout(0.5)
            self.fc2 = nn.Linear(256, 128)
            self.dropout2 = nn.Dropout(0.3)
            self.fc3 = nn.Linear(128, 64)
            self.dropout3 = nn.Dropout(0.2)
            self.fc4 = nn.Linear(64, num_classes)
        
        def forward(self, x):
            x = F.relu(self.fc1(x))
            x = self.dropout1(x)
            x = F.relu(self.fc2(x))
            x = self.dropout2(x)
            x = F.relu(self.fc3(x))
            x = self.dropout3(x)
            x = self.fc4(x)
            return x
    
    # Convert activity labels to integers
    activity_map = {'normal': 0, 'walking': 1, 'sitting': 2, 'standing': 3, 'fall': 4}
    y_train_int = np.array([activity_map[label] for label in y_train])
    y_test_int = np.array([activity_map[label] for label in y_test])
    
    model = MobilityMLP(X_train.shape[1], num_classes=5).to(device)
    
    # Prepare data
    X_train_tensor = torch.FloatTensor(X_train)
    y_train_tensor = torch.LongTensor(y_train_int)
    X_test_tensor = torch.FloatTensor(X_test)
    y_test_tensor = torch.LongTensor(y_test_int)
    
    # Create data loaders
    train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    
    # Training setup
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=10, factor=0.5)
    
    # Training loop
    model.train()
    for epoch in range(100):
        total_loss = 0
        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        
        avg_loss = total_loss / len(train_loader)
        scheduler.step(avg_loss)
        
        if epoch % 20 == 0:
            logger.info(f"Epoch {epoch}, Loss: {avg_loss:.4f}")
    
    # Evaluate
    model.eval()
    with torch.no_grad():
        test_pred = model(X_test_tensor)
        test_pred_labels = torch.argmax(test_pred, dim=1)
        test_accuracy = accuracy_score(y_test_int, test_pred_labels.numpy())
    
    logger.info(f"Mobility Model - Test Accuracy: {test_accuracy:.4f}")
    
    return model, {'accuracy': test_accuracy}

def train_model(model_type='respiration', params=None):
    """Main training function"""
    if params is None:
        params = {}
    
    # Set device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Using device: {device}")
    
    # Load data
    data, labels = load_synthetic_data()
    logger.info(f"Loaded {len(data)} samples")
    
    # Prepare data
    (X_train, X_test, y_resp_train, y_resp_test, 
     y_card_train, y_card_test, y_mob_train, y_mob_test, scaler) = prepare_data(data, labels)
    
    # Train models based on type
    if model_type == 'respiration':
        model, metrics = train_respiration_model(X_train, y_resp_train, X_test, y_resp_test, device)
    elif model_type == 'cardiac':
        model, metrics = train_cardiac_model(X_train, y_card_train, X_test, y_card_test, device)
    elif model_type == 'mobility':
        model, metrics = train_mobility_model(X_train, y_mob_train, X_test, y_mob_test, device)
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    # Save model
    model_dir = 'models'
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, f'{model_type}_model.pth')
    torch.save(model.state_dict(), model_path)
    
    # Save scaler
    scaler_path = os.path.join(model_dir, f'{model_type}_scaler.pkl')
    import pickle
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    
    logger.info(f"Model saved to {model_path}")
    
    return model_path, metrics

if __name__ == '__main__':
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Train all models
    for model_type in ['respiration', 'cardiac', 'mobility']:
        logger.info(f"Training {model_type} model...")
        model_path, metrics = train_model(model_type)
        logger.info(f"Training completed. Metrics: {metrics}")
