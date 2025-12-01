import torch
from torch import nn
import torch.nn.functional as F

class GRUWinProb(nn.Module):
    """
    Advanced GRU Model for Live Win Probability.
    Features:
    - Bidirectional GRU for better context
    - Attention mechanism to focus on key moments
    - Dropout for regularization
    - Layer Normalization
    """
    def __init__(self, input_size=1, hidden=128, num_layers=2, dropout=0.3):
        super().__init__()
        self.hidden_size = hidden
        self.num_layers = num_layers
        
        # Bidirectional GRU
        self.gru = nn.GRU(
            input_size, 
            hidden, 
            num_layers=num_layers, 
            batch_first=True, 
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        # Layer Norm
        self.ln = nn.LayerNorm(hidden * 2)
        
        # Attention Mechanism
        self.attention = nn.Sequential(
            nn.Linear(hidden * 2, hidden),
            nn.Tanh(),
            nn.Linear(hidden, 1)
        )
        
        # Output layers
        self.fc1 = nn.Linear(hidden * 2, 64)
        self.fc2 = nn.Linear(64, 1)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        # x: (batch, seq_len, input_size)
        
        # GRU Output: (batch, seq_len, hidden * 2)
        out, _ = self.gru(x)
        out = self.ln(out)
        
        # Attention weights
        # attn_weights: (batch, seq_len, 1)
        attn_weights = F.softmax(self.attention(out), dim=1)
        
        # Context vector (weighted sum of outputs)
        # context: (batch, hidden * 2)
        context = torch.sum(attn_weights * out, dim=1)
        
        # Classification head
        x = F.relu(self.fc1(context))
        x = self.dropout(x)
        logits = self.fc2(x)
        
        return torch.sigmoid(logits)
