"""Momentum Transformer for NBA prediction - treats a team's season as a sequence."""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class PositionalEncoding(nn.Module):
    """Sinusoidal positional encoding for game sequence position."""
    
    def __init__(self, d_model: int, max_len: int = 100, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)
        
        position = torch.arange(max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-math.log(10000.0) / d_model))
        
        pe = torch.zeros(max_len, d_model)
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        
        self.register_buffer('pe', pe.unsqueeze(0))  # (1, max_len, d_model)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Tensor of shape (batch, seq_len, d_model)
        """
        x = x + self.pe[:, :x.size(1), :]
        return self.dropout(x)


class MomentumTransformer(nn.Module):
    """Transformer for modeling team momentum from game sequences."""
    
    def __init__(
        self,
        input_dim: int = 5,          # Features per game: is_home, win, margin, rest, streak
        d_model: int = 64,           # Embedding dimension
        n_heads: int = 4,            # Attention heads
        n_layers: int = 4,           # Transformer layers  
        d_feedforward: int = 128,    # FFN hidden dim
        dropout: float = 0.15,
        max_seq_len: int = 20,       # Max games in sequence
    ):
        super().__init__()
        
        self.d_model = d_model
        
        # Project input features to embedding dimension
        self.input_projection = nn.Linear(input_dim, d_model)
        
        # Positional encoding
        self.pos_encoder = PositionalEncoding(d_model, max_seq_len, dropout)
        
        # Transformer encoder layers
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=n_heads,
            dim_feedforward=d_feedforward,
            dropout=dropout,
            batch_first=True,
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)
        
        # Output head: takes the [CLS]-equivalent (last position) to predict
        self.output_head = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model // 2, 1),
            nn.Sigmoid(),
        )
        
        self._init_weights()
        
        logger.info(f"MomentumTransformer initialized: d_model={d_model}, layers={n_layers}")
    
    def _init_weights(self):
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Tensor of shape (batch, seq_len, input_dim)
               Each element is a game with features [is_home, win, margin]
        
        Returns:
            Tensor of shape (batch, 1) with win probability for next game
        """
        # Project to embedding space
        x = self.input_projection(x)  # (batch, seq_len, d_model)
        
        # Add positional encoding
        x = self.pos_encoder(x)
        
        # Pass through Transformer
        x = self.transformer_encoder(x)  # (batch, seq_len, d_model)
        
        # Use the last position as the "summary" (like BERT [CLS])
        x = x[:, -1, :]  # (batch, d_model)
        
        # Predict next game outcome
        out = self.output_head(x)  # (batch, 1)
        
        return out.squeeze(-1)
    
    def get_momentum_score(self, x: torch.Tensor) -> float:
        """
        Convenience method for inference.
        
        Args:
            x: Tensor of shape (1, seq_len, input_dim) representing one team's history
        
        Returns:
            Float between 0-1 representing momentum/win probability
        """
        self.eval()
        with torch.no_grad():
            return self.forward(x).item()


class MomentumAnalytics:
    """High-level interface for using the Momentum Transformer in predictions."""
    
    def __init__(self, model_path: str = "artifacts/models/momentum/momentum_transformer_v2.pt"):
        self.model_path = model_path
        self.model = None
        self.loaded = False
        
        self._try_load()
    
    def _try_load(self):
        """Attempt to load a trained model, dynamically inferring architecture."""
        import os
        if os.path.exists(self.model_path):
            try:
                checkpoint = torch.load(self.model_path, map_location='cpu', weights_only=False)
                
                # Handle both wrapped and raw state dict formats
                if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
                    state_dict = checkpoint['model_state_dict']
                else:
                    state_dict = checkpoint
                
                # DYNAMICALLY INFER ARCHITECTURE FROM WEIGHTS
                ip_shape = state_dict['input_projection.weight'].shape
                d_model = ip_shape[0]
                input_dim = ip_shape[1]
                
                # Count layers
                n_layers = len(set(int(k.split('.')[2]) for k in state_dict.keys() if 'transformer_encoder.layers' in k))
                
                # Get FFN dim
                d_feedforward = state_dict['transformer_encoder.layers.0.linear1.weight'].shape[0]
                
                logger.info(f"MomentumTransformer initialized: d_model={d_model}, layers={n_layers}")
                
                # Infer max_seq_len from positional encoding
                max_seq_len = state_dict['pos_encoder.pe'].shape[1]
                
                self.model = MomentumTransformer(
                    input_dim=input_dim,
                    d_model=d_model,
                    n_heads=8 if d_model >= 128 else 4,  # More heads for larger d_model
                    n_layers=n_layers,
                    d_feedforward=d_feedforward,
                    max_seq_len=max_seq_len
                )

                self.model.load_state_dict(state_dict)
                self.model.eval()
                self.loaded = True
                logger.info("✅ MomentumTransformer loaded")
            except Exception as e:
                logger.warning(f"Failed to load Momentum model: {e}")
        else:
            logger.info("Momentum model not found, using simulated scores")

    
    def get_team_momentum_score(self, team: str, current_date: str = None, games_df = None) -> float:
        """
        Get the momentum score for a team based on their PAST games.
        
        Uses the trained Transformer model to analyze the team's recent game sequence.
        Returns score in [0.4, 0.6] range centered at 0.5.
        
        Args:
            team: Team name
            current_date: Date string (YYYY-MM-DD) - only use games BEFORE this date
            games_df: DataFrame with game history (optional, uses internal if not provided)
        """
        import torch
        import pandas as pd
        import numpy as np
        
        # If no date context, fall back to simulated (for backward compatibility)
        if current_date is None or games_df is None:
            from datetime import datetime
            seed = hash(team + datetime.now().strftime("%Y-%m-%d")) % 100
            return 0.5 + (seed - 50) / 500
        
        try:
            target_date = pd.to_datetime(current_date)
            
            # Get team's past games before this date
            team_games = games_df[
                ((games_df['home'] == team) | (games_df['away'] == team)) &
                (games_df['date'] < target_date)
            ].sort_values('date', ascending=True).tail(15)  # Last 15 games, chronological
            
            if len(team_games) < 1:
                # No games yet - return neutral
                return 0.5
            
            # Build feature sequence: [is_home, win, margin, rest, streak, fatigue, elo_prob] (7 features)
            sequence = []
            prev_date = None
            streak = 0
            recent_dates = []
            
            for _, game in team_games.iterrows():
                is_home = 1.0 if game['home'] == team else 0.0
                
                if is_home:
                    won = float(game['home_win'])
                    margin = float(game['margin']) / 50.0  # Normalize (match training)
                else:
                    won = 1.0 - float(game['home_win'])
                    margin = -float(game['margin']) / 50.0
                
                # Rest days
                if prev_date is not None:
                    rest = (game['date'] - prev_date).days
                    rest = max(rest, 0)
                    rest = min(rest, 7) / 7.0  # Normalize to [0, 1]
                else:
                    rest = 0.5
                
                # Streak BEFORE current game (match training behavior)
                streak_norm = np.clip(streak / 10.0, -1, 1)
                
                # Fatigue: match historical_2024/pregame_full definition
                # home_fatigue_score = games_last_7 * 0.5 + 2.0 * (rest_days <= 1)
                cutoff = game['date'] - pd.Timedelta(days=7)
                games_last_7 = sum(1 for dt in recent_dates if dt > cutoff)
                fatigue_score = games_last_7 * 0.5 + (1.0 if rest <= (1.0 / 7.0) else 0.0) * 2.0
                fatigue = min(fatigue_score / 5.0, 1.0)
                
                # ELO probability (use stored value or estimate)
                if 'elo_p_home' in game:
                    elo_prob = float(game['elo_p_home'])
                    if not is_home:
                        elo_prob = 1.0 - elo_prob
                else:
                    elo_prob = float(game.get('elo_win_prob', 0.5))
                    if not is_home:
                        elo_prob = 1.0 - elo_prob
                
                sequence.append([is_home, won, margin, rest, streak_norm, fatigue, elo_prob])
                
                # Update streak AFTER current game
                if won > 0.5:
                    streak = max(streak, 0) + 1
                else:
                    streak = min(streak, 0) - 1
                
                recent_dates.append(game['date'])
                prev_date = game['date']
            
            # Already chronological and capped to last 15 games
            
            if self.loaded and self.model is not None:
                # Run through trained Transformer
                with torch.no_grad():
                    x = torch.tensor([sequence], dtype=torch.float32)
                    # Pad if needed
                    if x.shape[1] < 15:
                        pad = torch.zeros(1, 15 - x.shape[1], 7)  # 7 features now
                        x = torch.cat([pad, x], dim=1)
                    
                    output = self.model(x)
                    prob = output.item()
                    # Map to [0.4, 0.6] range
                    return 0.4 + prob * 0.2
            else:
                # Fallback: Simple win rate based score
                win_rate = sum(1 for g in sequence if g[1] > 0.5) / len(sequence)
                return 0.4 + win_rate * 0.2
                
        except Exception as e:
            logger.warning(f"Momentum calculation error for {team}: {e}")
            return 0.5
    
    def get_matchup_momentum_delta(self, home_team: str, away_team: str, 
                                     current_date: str = None, games_df = None) -> tuple:
        """
        Calculate momentum-based adjustment to win probability.
        
        Args:
            home_team: Home team name
            away_team: Away team name  
            current_date: Date string (YYYY-MM-DD) for pregame-only calculation
            games_df: DataFrame with game history
        
        Returns:
            delta (float): Probability adjustment
            metadata (dict): Context for explainability
        """
        home_momentum = self.get_team_momentum_score(home_team, current_date, games_df)
        away_momentum = self.get_team_momentum_score(away_team, current_date, games_df)
        
        diff = home_momentum - away_momentum
        
        # Weight factor (Sharpened for v4.1: 0.25)
        MOMENTUM_WEIGHT = 0.25
        delta = diff * MOMENTUM_WEIGHT
        delta = max(-0.05, min(0.05, delta))  # Clip to ±5%
        
        metadata = {
            "home_momentum": round(home_momentum, 3),
            "away_momentum": round(away_momentum, 3),
            "applied_delta": round(delta, 4),
        }
        
        logger.info(f"📈 Momentum: {home_team} ({home_momentum:.2f}) vs {away_team} ({away_momentum:.2f}) -> Delta: {delta:+.4f}")
        
        return delta, metadata


# Global instance for pipeline integration
momentum_analytics = MomentumAnalytics()
