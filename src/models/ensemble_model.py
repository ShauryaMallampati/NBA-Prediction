"""
NBA Ensemble Model System
5+ ML algorithms voting together for predictions with win probabilities
"""

import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Any
import joblib
from datetime import datetime

# Machine Learning models
from sklearn.ensemble import (
    RandomForestClassifier,
    GradientBoostingClassifier,
    VotingClassifier,
    StackingClassifier
)
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import xgboost as xgb

logger = logging.getLogger(__name__)


class NBAEnsembleModel:
    """
    Ensemble model combining 5+ ML algorithms:
    1. XGBoost
    2. Random Forest
    3. Decision Tree
    4. Logistic Regression
    5. Gradient Boosting
    6. Neural Network (MLP)
    
    Models vote together to predict game outcomes with win probabilities
    """
    
    def __init__(self, model_dir: str = "models/ensemble"):
        """Initialize ensemble model system"""
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.scaler = StandardScaler()
        self.models = {}
        self.ensemble = None
        self.stacking_ensemble = None
        self.feature_names = []
        self.is_trained = False
        
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize all base models"""
        logger.info("Initializing ensemble models...")
        
        # 1. XGBoost - Powerful gradient boosting
        self.models['xgboost'] = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            objective='binary:logistic',
            random_state=42,
            eval_metric='logloss'
        )
        
        # 2. Random Forest - Ensemble of decision trees
        self.models['random_forest'] = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        # 3. Decision Tree - Simple but interpretable
        self.models['decision_tree'] = DecisionTreeClassifier(
            max_depth=10,
            min_samples_split=10,
            min_samples_leaf=4,
            random_state=42
        )
        
        # 4. Logistic Regression - Linear model baseline
        self.models['logistic_regression'] = LogisticRegression(
            max_iter=1000,
            C=1.0,
            random_state=42,
            n_jobs=-1
        )
        
        # 5. Gradient Boosting - Sequential ensemble
        self.models['gradient_boosting'] = GradientBoostingClassifier(
            n_estimators=150,
            learning_rate=0.1,
            max_depth=5,
            subsample=0.8,
            random_state=42
        )
        
        # 6. Neural Network (MLP) - Deep learning approach
        self.models['neural_network'] = MLPClassifier(
            hidden_layer_sizes=(64, 32),
            activation='relu',
            solver='adam',
            alpha=0.0001,
            batch_size='auto',
            learning_rate='adaptive',
            max_iter=500,
            random_state=42,
            early_stopping=False,  # Disabled for small datasets
            validation_fraction=0.1
        )
        
        logger.info(f"✅ Initialized {len(self.models)} base models")
    
    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        use_stacking: bool = True
    ) -> Dict[str, float]:
        """
        Train all models and create voting/stacking ensemble
        
        Args:
            X: Feature matrix
            y: Target labels (1 for home win, 0 for away win)
            use_stacking: Use stacking ensemble (more powerful)
            
        Returns:
            Dictionary of model accuracies
        """
        logger.info("="*80)
        logger.info("🚀 TRAINING ENSEMBLE MODEL SYSTEM")
        logger.info("="*80)
        
        # Store feature names
        self.feature_names = list(X.columns)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        logger.info(f"\n📊 Dataset Info:")
        logger.info(f"   Training samples: {len(X_train)}")
        logger.info(f"   Testing samples: {len(X_test)}")
        logger.info(f"   Features: {len(self.feature_names)}")
        logger.info(f"   Class balance: {dict(y.value_counts())}")
        
        # Scale features
        logger.info("\n🔄 Scaling features...")
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train individual models
        results = {}
        predictions = {}
        
        logger.info("\n" + "="*80)
        logger.info("🎯 TRAINING INDIVIDUAL MODELS")
        logger.info("="*80)
        
        for name, model in self.models.items():
            logger.info(f"\n📈 Training {name.replace('_', ' ').title()}...")
            
            try:
                # Train model
                model.fit(X_train_scaled, y_train)
                
                # Predict
                y_pred = model.predict(X_test_scaled)
                predictions[name] = y_pred
                
                # Calculate accuracy
                accuracy = accuracy_score(y_test, y_pred)
                results[name] = accuracy
                
                # Cross-validation score
                cv_scores = cross_val_score(
                    model, X_train_scaled, y_train, cv=5, scoring='accuracy'
                )
                
                logger.info(f"   ✅ Test Accuracy: {accuracy:.4f}")
                logger.info(f"   📊 CV Score: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
                
            except Exception as e:
                logger.error(f"   ❌ Error training {name}: {e}")
                results[name] = 0.0
        
        # Create Voting Ensemble
        logger.info("\n" + "="*80)
        logger.info("🗳️  CREATING VOTING ENSEMBLE")
        logger.info("="*80)
        
        estimators = [(name, model) for name, model in self.models.items()]
        
        self.ensemble = VotingClassifier(
            estimators=estimators,
            voting='soft',  # Use probability predictions
            n_jobs=-1
        )
        
        logger.info("\n📈 Training Voting Ensemble...")
        self.ensemble.fit(X_train_scaled, y_train)
        
        y_pred_ensemble = self.ensemble.predict(X_test_scaled)
        ensemble_accuracy = accuracy_score(y_test, y_pred_ensemble)
        results['voting_ensemble'] = ensemble_accuracy
        
        logger.info(f"   ✅ Voting Ensemble Accuracy: {ensemble_accuracy:.4f}")
        
        # Create Stacking Ensemble (meta-learner)
        if use_stacking:
            logger.info("\n" + "="*80)
            logger.info("🏗️  CREATING STACKING ENSEMBLE")
            logger.info("="*80)
            
            self.stacking_ensemble = StackingClassifier(
                estimators=estimators,
                final_estimator=LogisticRegression(random_state=42),
                cv=5,
                n_jobs=-1
            )
            
            logger.info("\n📈 Training Stacking Ensemble...")
            self.stacking_ensemble.fit(X_train_scaled, y_train)
            
            y_pred_stacking = self.stacking_ensemble.predict(X_test_scaled)
            stacking_accuracy = accuracy_score(y_test, y_pred_stacking)
            results['stacking_ensemble'] = stacking_accuracy
            
            logger.info(f"   ✅ Stacking Ensemble Accuracy: {stacking_accuracy:.4f}")
        
        # Print Summary
        logger.info("\n" + "="*80)
        logger.info("📊 MODEL PERFORMANCE SUMMARY")
        logger.info("="*80)
        
        sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
        for i, (model_name, accuracy) in enumerate(sorted_results, 1):
            stars = "⭐" * min(5, int(accuracy * 5))
            logger.info(f"{i}. {model_name.replace('_', ' ').title():30s} {accuracy:.4f} {stars}")
        
        # Mark as trained
        self.is_trained = True
        
        # Save models
        self.save()
        
        logger.info("\n" + "="*80)
        logger.info("✅ ENSEMBLE MODEL TRAINING COMPLETE!")
        logger.info("="*80)
        
        return results
    
    def predict(self, X: pd.DataFrame) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Predict game outcomes with ensemble voting
        
        Args:
            X: Feature matrix
            
        Returns:
            Tuple of (predictions, detailed_results)
            predictions: Binary predictions (1=home win, 0=away win)
            detailed_results: Dictionary with probabilities and individual votes
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        # Scale features
        X_scaled = self.scaler.transform(X)
        
        # Get predictions from all models
        individual_predictions = {}
        individual_probabilities = {}
        
        for name, model in self.models.items():
            try:
                pred = model.predict(X_scaled)
                proba = model.predict_proba(X_scaled)
                individual_predictions[name] = pred
                individual_probabilities[name] = proba
            except Exception as e:
                logger.error(f"Error predicting with {name}: {e}")
        
        # Ensemble predictions
        ensemble_pred = self.ensemble.predict(X_scaled)
        ensemble_proba = self.ensemble.predict_proba(X_scaled)
        
        # Stacking predictions (if available)
        if self.stacking_ensemble:
            stacking_pred = self.stacking_ensemble.predict(X_scaled)
            stacking_proba = self.stacking_ensemble.predict_proba(X_scaled)
        else:
            stacking_pred = ensemble_pred
            stacking_proba = ensemble_proba
        
        # Calculate consensus and confidence
        all_votes = np.array([pred for pred in individual_predictions.values()])
        vote_counts = np.sum(all_votes, axis=0)
        consensus_strength = vote_counts / len(self.models)
        
        # Detailed results
        detailed_results = {
            'individual_predictions': individual_predictions,
            'individual_probabilities': individual_probabilities,
            'voting_ensemble_prediction': ensemble_pred,
            'voting_ensemble_probability': ensemble_proba,
            'stacking_ensemble_prediction': stacking_pred,
            'stacking_ensemble_probability': stacking_proba,
            'consensus_strength': consensus_strength,
            'model_agreement': np.mean([
                np.mean(pred == stacking_pred) for pred in individual_predictions.values()
            ])
        }
        
        # Use stacking ensemble as final prediction (most powerful)
        return stacking_pred, detailed_results
    
    def predict_with_probabilities(
        self,
        X: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Predict with detailed probability breakdown
        
        Returns DataFrame with:
        - Final prediction
        - Win probability for each team
        - Individual model votes
        - Confidence score
        """
        predictions, details = self.predict(X)
        
        results = []
        stacking_proba = details['stacking_ensemble_probability']
        
        for i in range(len(X)):
            # Get individual model votes
            votes = {
                name: int(pred[i]) 
                for name, pred in details['individual_predictions'].items()
            }
            
            # Calculate consensus
            total_votes = sum(votes.values())
            consensus_pct = total_votes / len(votes) * 100
            
            # Win probabilities
            home_win_prob = stacking_proba[i][1] * 100  # Class 1 = home win
            away_win_prob = stacking_proba[i][0] * 100  # Class 0 = away win
            
            # Confidence (how much models agree)
            confidence = abs(home_win_prob - 50) / 50 * 100  # 0-100%
            
            results.append({
                'prediction': 'HOME_WIN' if predictions[i] == 1 else 'AWAY_WIN',
                'home_win_probability': round(home_win_prob, 2),
                'away_win_probability': round(away_win_prob, 2),
                'confidence': round(confidence, 2),
                'models_agree': f"{total_votes}/{len(votes)}",
                'consensus_percentage': round(consensus_pct, 2),
                **{f'{name}_vote': 'HOME' if vote == 1 else 'AWAY' 
                   for name, vote in votes.items()}
            })
        
        return pd.DataFrame(results)
    
    def save(self):
        """Save all models and scaler"""
        logger.info(f"\n💾 Saving ensemble models to {self.model_dir}")
        
        # Save individual models
        for name, model in self.models.items():
            joblib.dump(model, self.model_dir / f"{name}.pkl")
        
        # Save ensembles
        joblib.dump(self.ensemble, self.model_dir / "voting_ensemble.pkl")
        if self.stacking_ensemble:
            joblib.dump(self.stacking_ensemble, self.model_dir / "stacking_ensemble.pkl")
        
        # Save scaler and metadata
        joblib.dump(self.scaler, self.model_dir / "scaler.pkl")
        
        metadata = {
            'feature_names': self.feature_names,
            'num_models': len(self.models),
            'model_names': list(self.models.keys()),
            'trained_at': datetime.now().isoformat(),
            'is_trained': self.is_trained
        }
        
        import json
        with open(self.model_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info("✅ Models saved successfully")
    
    def load(self):
        """Load saved models"""
        logger.info(f"\n📥 Loading ensemble models from {self.model_dir}")
        
        try:
            # Load metadata
            import json
            with open(self.model_dir / "metadata.json", 'r') as f:
                metadata = json.load(f)
            
            self.feature_names = metadata['feature_names']
            self.is_trained = metadata['is_trained']
            
            # Load individual models
            for name in metadata['model_names']:
                self.models[name] = joblib.load(self.model_dir / f"{name}.pkl")
            
            # Load ensembles
            self.ensemble = joblib.load(self.model_dir / "voting_ensemble.pkl")
            
            if (self.model_dir / "stacking_ensemble.pkl").exists():
                self.stacking_ensemble = joblib.load(self.model_dir / "stacking_ensemble.pkl")
            
            # Load scaler
            self.scaler = joblib.load(self.model_dir / "scaler.pkl")
            
            logger.info(f"✅ Loaded {len(self.models)} models successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading models: {e}")
            return False


# Global instance
ensemble_model = NBAEnsembleModel()
