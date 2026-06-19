"""
Machine learning models for health monitoring
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

class RespirationCNN(nn.Module):
    """CNN model for respiration rate estimation"""
    def __init__(self, input_channels=1, sequence_length=1000):
        super(RespirationCNN, self).__init__()
        
        self.conv1 = nn.Conv1d(input_channels, 32, kernel_size=7, padding=3)
        self.bn1 = nn.BatchNorm1d(32)
        self.pool1 = nn.MaxPool1d(2)
        
        self.conv2 = nn.Conv1d(32, 64, kernel_size=5, padding=2)
        self.bn2 = nn.BatchNorm1d(64)
        self.pool2 = nn.MaxPool1d(2)
        
        self.conv3 = nn.Conv1d(64, 128, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm1d(128)
        self.pool3 = nn.MaxPool1d(2)
        
        # Calculate the size after convolutions
        conv_output_size = sequence_length // 8 * 128
        
        self.fc1 = nn.Linear(conv_output_size, 256)
        self.dropout1 = nn.Dropout(0.5)
        self.fc2 = nn.Linear(256, 64)
        self.dropout2 = nn.Dropout(0.3)
        self.fc3 = nn.Linear(64, 1)  # Output respiration rate
        
    def forward(self, x):
        x = F.relu(self.bn1(self.conv1(x)))
        x = self.pool1(x)
        
        x = F.relu(self.bn2(self.conv2(x)))
        x = self.pool2(x)
        
        x = F.relu(self.bn3(self.conv3(x)))
        x = self.pool3(x)
        
        x = x.view(x.size(0), -1)  # Flatten
        
        x = F.relu(self.fc1(x))
        x = self.dropout1(x)
        x = F.relu(self.fc2(x))
        x = self.dropout2(x)
        x = self.fc3(x)
        
        return x

class CardiacLSTM(nn.Module):
    """LSTM model for cardiac metrics estimation"""
    def __init__(self, input_size=1, hidden_size=64, num_layers=2):
        super(CardiacLSTM, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, 
                           batch_first=True, dropout=0.2)
        
        self.fc1 = nn.Linear(hidden_size, 128)
        self.dropout1 = nn.Dropout(0.5)
        self.fc2 = nn.Linear(128, 64)
        self.dropout2 = nn.Dropout(0.3)
        self.fc3 = nn.Linear(64, 2)  # Output heart rate and HRV
        
    def forward(self, x):
        # Initialize hidden state
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        
        # Forward propagate LSTM
        out, _ = self.lstm(x, (h0, c0))
        
        # Take the last output
        out = out[:, -1, :]
        
        # Apply fully connected layers
        out = F.relu(self.fc1(out))
        out = self.dropout1(out)
        out = F.relu(self.fc2(out))
        out = self.dropout2(out)
        out = self.fc3(out)
        
        return out

class MobilityTCN(nn.Module):
    """Temporal Convolutional Network for mobility classification"""
    def __init__(self, input_channels=1, num_classes=5):
        super(MobilityTCN, self).__init__()
        
        self.tcn = nn.Sequential(
            nn.Conv1d(input_channels, 64, kernel_size=3, padding=1),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.2),
            
            nn.Conv1d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.2),
            
            nn.Conv1d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.2),
            
            nn.AdaptiveAvgPool1d(1)
        )
        
        self.classifier = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(128, num_classes)
        )
        
    def forward(self, x):
        x = self.tcn(x)
        x = x.view(x.size(0), -1)
        x = self.classifier(x)
        return x

class HealthMonitoringEnsemble(nn.Module):
    """Ensemble model combining all health monitoring models"""
    def __init__(self, respiration_model, cardiac_model, mobility_model):
        super(HealthMonitoringEnsemble, self).__init__()
        
        self.respiration_model = respiration_model
        self.cardiac_model = cardiac_model
        self.mobility_model = mobility_model
        
        # Fusion layer
        self.fusion = nn.Sequential(
            nn.Linear(4, 32),  # 1 (respiration) + 2 (cardiac) + 1 (mobility)
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1)  # Risk score
        )
        
    def forward(self, x):
        # Get predictions from individual models
        respiration_pred = self.respiration_model(x)
        cardiac_pred = self.cardiac_model(x)
        mobility_pred = self.mobility_model(x)
        
        # Combine predictions
        combined = torch.cat([
            respiration_pred,
            cardiac_pred,
            mobility_pred
        ], dim=1)
        
        # Calculate risk score
        risk_score = self.fusion(combined)
        
        return {
            'respiration_rate': respiration_pred,
            'heart_rate': cardiac_pred[:, 0:1],
            'hrv': cardiac_pred[:, 1:2],
            'activity_label': mobility_pred,
            'risk_score': risk_score
        }

def create_models(device='cpu'):
    """Create and initialize all models"""
    respiration_model = RespirationCNN()
    cardiac_model = CardiacLSTM()
    mobility_model = MobilityTCN()
    
    ensemble_model = HealthMonitoringEnsemble(
        respiration_model, cardiac_model, mobility_model
    )
    
    return {
        'respiration': respiration_model.to(device),
        'cardiac': cardiac_model.to(device),
        'mobility': mobility_model.to(device),
        'ensemble': ensemble_model.to(device)
    }
