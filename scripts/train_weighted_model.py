#!/usr/bin/env python3
"""
Weighted NBA Model Training
Uses ALL 135K games but weights them intelligently:
  - More weight on recent games (2020-2025)
  - More weight on games with complete features
  - Gradual decay for older games
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import xgboost as xgb
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WeightedModelTrainer:
    """Train XGBoost with intelligent sample weighting"""
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.weights = None
        
    def load_all_games(self):
        """Load all 135K games (raw historical data)"""
        logger.info("📂 Loading all historical games...")
        
        data_path = Path(__file__).parent.parent / "data" / "raw"
        
        # Try different possible locations
        candidates = [
            data_path / "all_games_historical.csv",
            data_path / "games.csv",
            data_path / "all_games.csv",
            Path(__file__).parent.parent / "data" / "processed" / "all_games.csv",
        ]
        
        games_file = None
        for candidate in candidates:
            if candidate.exists():
                games_file = candidate
                logger.info(f"✅ Found games file: {games_file}")
                break
        
        if games_file is None:
            # Generate synthetic 135K games for demo
            logger.warning("⚠️  No games file found, generating synthetic 135K games...")
            return self._generate_synthetic_games(135588)
        
        # Load CSV
        df = pd.read_csv(games_file, low_memory=False)
        logger.info(f"✅ Loaded {len(df):,} games")
        
        return df
    
    def _generate_synthetic_games(self, n_games):
        """Generate realistic synthetic games"""
        logger.info(f"Generating {n_games:,} synthetic games...")
        
        np.random.seed(42)
        dates = pd.date_range(start='1952-01-01', end='2025-01-01', periods=n_games)
        
        teams = ['LAL', 'BOS', 'CHI', 'GSW', 'MIA', 'NYK', 'LAC', 'DEN', 
                 'SAS', 'OKC', 'HOU', 'PHI', 'MIL', 'TOR', 'DAL', 'MIN',
                 'PHX', 'BRK', 'ATL', 'MEM', 'UTA', 'NOP', 'SAC', 'POR']
        
        data = {
            'date': dates,
            'home_team': np.random.choice(teams, n_games),
            'away_team': np.random.choice(teams, n_games),
            'home_score': np.random.randint(80, 140, n_games),
            'away_score': np.random.randint(80, 140, n_games),
            'home_elo': np.random.normal(1500, 200, n_games),
            'away_elo': np.random.normal(1500, 200, n_games),
            'home_rest': np.random.randint(0, 5, n_games),
            'away_rest': np.random.randint(0, 5, n_games),
        }
        
        df = pd.DataFrame(data)
        df['home_win'] = (df['home_score'] > df['away_score']).astype(int)
        
        logger.info(f"✅ Generated {len(df):,} synthetic games (1952-2025)")
        
        return df
    
    def engineer_features(self, df):
        """Engineer features, handling both complete and partial data"""
        logger.info("⚙️  Engineering features...")
        
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date'])
        
        # Basic features (available for most games)
        if 'home_elo' not in df.columns:
            # Estimate Elo if missing (for older games)
            df['home_elo'] = 1500 + np.random.normal(0, 200, len(df))
            df['away_elo'] = 1500 + np.random.normal(0, 200, len(df))
        
        # Ensure all required columns exist (fill with defaults if missing)
        required_cols = {
            'home_rest': 2,
            'away_rest': 2,
            'home_win': 0,
            'away_win': 0,
            'home_last_5_wins': 2,
            'away_last_5_wins': 2,
        }
        
        for col, default_val in required_cols.items():
            if col not in df.columns:
                df[col] = default_val
        
        # Feature engineering
        df['elo_diff'] = df['home_elo'] - df['away_elo']
        df['elo_win_prob'] = 1 / (1 + 10 ** (-df['elo_diff'] / 400))
        df['rest_diff'] = df['home_rest'] - df['away_rest']
        df['home_form'] = df['home_last_5_wins'] / 5.0
        df['away_form'] = df['away_last_5_wins'] / 5.0
        df['form_diff'] = df['home_form'] - df['away_form']
        
        # Fill any NaN values
        df = df.fillna(df.mean(numeric_only=True))
        
        logger.info(f"✅ Engineered features for {len(df):,} games")
        
        return df
    
    def calculate_sample_weights(self, df):
        """
        Calculate weights for each game:
        1. Newer games get higher weight (recency)
        2. Complete-feature games get higher weight
        3. Older games get lower weight (gradual decay)
        """
        logger.info("⚙️  Calculating sample weights...")
        
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        
        # Get date range
        min_date = df['date'].min()
        max_date = df['date'].max()
        total_days = (max_date - min_date).days
        
        # Weight 1: Recency (newer = higher weight)
        # Exponential decay: recent games get 1.0, old games get 0.1
        df['days_ago'] = (max_date - df['date']).dt.days
        recency_weight = np.exp(-df['days_ago'] / (total_days / 3))  # 1/3 life decay
        recency_weight = (recency_weight - recency_weight.min()) / (recency_weight.max() - recency_weight.min())
        recency_weight = 0.5 + (recency_weight * 0.5)  # Range: 0.5 to 1.0
        
        # Weight 2: Feature completeness
        # More non-null features = higher weight
        feature_weight = df.notna().sum(axis=1) / len(df.columns)
        feature_weight = 0.8 + (feature_weight * 0.2)  # Range: 0.8 to 1.0
        
        # Combined weight
        combined_weight = recency_weight * feature_weight
        
        # Normalize to sum to n_samples (for proper XGBoost interpretation)
        combined_weight = combined_weight / combined_weight.mean()
        
        logger.info(f"✅ Calculated weights:")
        logger.info(f"   Recent games (2020-2025): {combined_weight[df['date'] >= '2020-01-01'].mean():.2f}x")
        logger.info(f"   Old games (1952-2000): {combined_weight[df['date'] < '2000-01-01'].mean():.2f}x")
        logger.info(f"   Mean weight: {combined_weight.mean():.2f}")
        logger.info(f"   Max weight: {combined_weight.max():.2f}")
        logger.info(f"   Min weight: {combined_weight.min():.2f}")
        
        return combined_weight.values
    
    def train_weighted_model(self, X_train, y_train, sample_weight):
        """Train XGBoost with sample weights"""
        logger.info("🚀 Training weighted XGBoost...")
        
        self.model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric='logloss',
            n_jobs=-1,
            verbosity=0,
        )
        
        # Train with sample weights
        self.model.fit(
            X_train, y_train,
            sample_weight=sample_weight,
            verbose=False,
        )
        
        logger.info("✅ Model trained with weighted samples")
        
        return self.model
    
    def evaluate(self, X_test, y_test, name="Test Set"):
        """Evaluate model"""
        y_pred = self.model.predict(X_test)
        y_proba = self.model.predict_proba(X_test)[:, 1]
        
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        roc_auc = roc_auc_score(y_test, y_proba)
        
        logger.info(f"\n📊 {name} Metrics:")
        logger.info(f"   Accuracy:  {accuracy:.4f}")
        logger.info(f"   Precision: {precision:.4f}")
        logger.info(f"   Recall:    {recall:.4f}")
        logger.info(f"   F1-Score:  {f1:.4f}")
        logger.info(f"   ROC-AUC:   {roc_auc:.4f}")
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'roc_auc': roc_auc,
        }
    
    def run(self):
        """Main training pipeline"""
        print("\n" + "=" * 100)
        print("🏀 WEIGHTED MODEL TRAINING - ALL 135K GAMES")
        print("=" * 100)
        
        # Load all games
        df_all = self.load_all_games()
        print(f"\n📊 Total games available: {len(df_all):,}")
        
        # Engineer features
        df_features = self.engineer_features(df_all)
        print(f"✅ Features engineered for {len(df_features):,} games")
        
        # Calculate weights
        weights = self.calculate_sample_weights(df_features)
        
        # Prepare data
        feature_cols = [col for col in df_features.columns 
                       if col not in ['date', 'home_team', 'away_team', 'home_win', 'away_win']]
        
        X = df_features[feature_cols].fillna(0)
        y = df_features['home_win'].astype(int)
        
        # Time-series split (proper for sports)
        tscv = TimeSeriesSplit(n_splits=3)
        split_idx = list(tscv.split(X))[0][1]  # Use last split
        
        train_indices = list(tscv.split(X))[0][0]
        test_indices = list(tscv.split(X))[0][1]
        
        X_train, X_test = X.iloc[train_indices], X.iloc[test_indices]
        y_train, y_test = y.iloc[train_indices], y.iloc[test_indices]
        sample_weights_train = weights[train_indices]
        
        print(f"\n📈 Data split:")
        print(f"   Training: {len(X_train):,} games")
        print(f"   Testing:  {len(X_test):,} games")
        print(f"   Date range: {df_features.iloc[train_indices]['date'].min().date()} → {df_features.iloc[test_indices]['date'].max().date()}")
        
        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train weighted model
        self.train_weighted_model(X_train_scaled, y_train, sample_weights_train)
        
        # Evaluate
        metrics = self.evaluate(X_test_scaled, y_test, "Test Set")
        
        # Compare to baseline
        print(f"\n📊 Comparison to baseline (63.83%):")
        improvement = (metrics['accuracy'] - 0.6383) * 100
        print(f"   {'🔥 IMPROVEMENT' if improvement > 0 else '❌ DECLINE'}: {improvement:+.2f}%")
        print(f"   New accuracy: {metrics['accuracy']:.4f}")
        
        # Show feature importance
        print(f"\n🎯 Top 10 Important Features:")
        importance_df = pd.DataFrame({
            'feature': feature_cols,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        for i, row in importance_df.head(10).iterrows():
            print(f"   {row['feature']:20s} {row['importance']:8.4f}")
        
        # Weight analysis
        print(f"\n⚖️  Weight Analysis:")
        df_weighted = df_features.copy()
        df_weighted['weight'] = weights
        
        for year_threshold in [1990, 2000, 2010, 2015, 2020]:
            recent = df_weighted[df_weighted['date'] >= f'{year_threshold}-01-01']
            if len(recent) > 0:
                avg_weight = recent['weight'].mean()
                print(f"   Games since {year_threshold}: {avg_weight:.2f}x weight")
        
        print("\n" + "=" * 100)
        print("✅ WEIGHTED TRAINING COMPLETE")
        print("=" * 100)
        
        return metrics, importance_df


def main():
    trainer = WeightedModelTrainer()
    metrics, importance = trainer.run()


if __name__ == "__main__":
    main()
