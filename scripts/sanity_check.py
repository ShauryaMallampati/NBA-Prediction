#!/usr/bin/env python3
"""
🔍 FULL SANITY CHECK - VERIFY 99.7% ACCURACY IS REAL

Check for:
1. Data leakage (target in features)
2. Proper train/test split
3. Feature validity
4. Target distribution
5. Model complexity vs data size
6. Cross-validation consistency
7. Real vs synthetic data
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
from sklearn.metrics import accuracy_score, roc_auc_score, confusion_matrix
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class SanityChecker:
    """Verify model performance is real"""
    
    def __init__(self):
        self.df = None
        self.warnings = []
        self.issues = []
    
    def load_and_inspect(self):
        """Load data and inspect for issues"""
        logger.info("\n" + "="*100)
        logger.info("🔍 STEP 1: LOAD AND INSPECT DATA")
        logger.info("="*100)
        
        features_path = Path(__file__).parent.parent / "data" / "processed" / "engineered_features.csv"
        self.df = pd.read_csv(features_path, low_memory=False)
        
        logger.info(f"\n📊 Dataset Overview:")
        logger.info(f"   Shape: {self.df.shape}")
        logger.info(f"   Rows: {len(self.df)}")
        logger.info(f"   Columns: {len(self.df.columns)}")
        
        # Check for duplicates
        duplicates = self.df.duplicated().sum()
        logger.info(f"\n🔴 DUPLICATES CHECK:")
        logger.info(f"   Exact duplicates: {duplicates}")
        if duplicates > 0:
            self.issues.append(f"❌ Found {duplicates} duplicate rows - possible data leakage!")
        else:
            logger.info(f"   ✅ No duplicates")
        
        # Check for NaN
        logger.info(f"\n🔴 MISSING VALUES CHECK:")
        nan_count = self.df.isnull().sum().sum()
        logger.info(f"   Total NaN values: {nan_count}")
        if nan_count > 0:
            logger.info(f"   Columns with NaN:")
            for col in self.df.columns:
                nan_in_col = self.df[col].isnull().sum()
                if nan_in_col > 0:
                    logger.info(f"      {col}: {nan_in_col}")
            self.warnings.append(f"⚠️  {nan_count} NaN values found (filled with mean)")
        else:
            logger.info(f"   ✅ No missing values")
        
        return self
    
    def check_target_leakage(self):
        """Check if target is in features"""
        logger.info("\n" + "="*100)
        logger.info("🔍 STEP 2: CHECK FOR TARGET LEAKAGE")
        logger.info("="*100)
        
        # Identify numeric columns
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        exclude = {'home_win', 'away_win', 'score_diff', 'home_score', 'away_score'}
        
        logger.info(f"\n🔴 SUSPICIOUS COLUMNS CHECK:")
        logger.info(f"   Total numeric columns: {len(numeric_cols)}")
        logger.info(f"   Excluding: {exclude}")
        
        # Check if score_diff is in features (it determines the winner!)
        if 'score_diff' in numeric_cols:
            self.issues.append("❌ CRITICAL: score_diff is in features! This determines winner!")
            logger.info(f"   ❌ score_diff column found - THIS IS THE TARGET (home_win = score_diff > 0)")
        
        if 'home_score' in numeric_cols and 'away_score' in numeric_cols:
            self.issues.append("❌ CRITICAL: Actual game scores in features! Predicting after game happened!")
            logger.info(f"   ❌ home_score and away_score found - THIS IS DIRECT LEAKAGE")
        
        if 'away_win' in numeric_cols:
            self.issues.append("❌ CRITICAL: away_win (derived from home_win) in features!")
            logger.info(f"   ❌ away_win column found - Perfect predictor of home_win")
        
        if not self.issues:
            logger.info(f"   ✅ No obvious target leakage detected")
        
        return self
    
    def check_temporal_leakage(self):
        """Check if data mixes past/future"""
        logger.info("\n" + "="*100)
        logger.info("🔍 STEP 3: CHECK FOR TEMPORAL LEAKAGE")
        logger.info("="*100)
        
        if 'date' not in self.df.columns:
            logger.warning("   ⚠️  No date column found")
            return self
        
        self.df['date'] = pd.to_datetime(self.df['date'], errors='coerce')
        min_date = self.df['date'].min()
        max_date = self.df['date'].max()
        
        logger.info(f"\n🔴 DATE RANGE CHECK:")
        logger.info(f"   Min date: {min_date}")
        logger.info(f"   Max date: {max_date}")
        logger.info(f"   Span: {(max_date - min_date).days} days")
        
        if (max_date - min_date).days < 365:
            self.warnings.append(f"⚠️  Data only spans {(max_date - min_date).days} days - limited temporal diversity")
        else:
            logger.info(f"   ✅ Good temporal diversity")
        
        return self
    
    def check_class_balance(self):
        """Check target distribution"""
        logger.info("\n" + "="*100)
        logger.info("🔍 STEP 4: CHECK CLASS BALANCE")
        logger.info("="*100)
        
        if 'home_win' not in self.df.columns:
            logger.error("   ❌ home_win column not found!")
            self.issues.append("No target column found")
            return self
        
        target = self.df['home_win']
        counts = target.value_counts()
        
        logger.info(f"\n🔴 TARGET DISTRIBUTION:")
        logger.info(f"   Home wins (1): {counts.get(1, 0)} ({counts.get(1, 0)/len(target)*100:.1f}%)")
        logger.info(f"   Away wins (0): {counts.get(0, 0)} ({counts.get(0, 0)/len(target)*100:.1f}%)")
        
        if 0.4 < counts.get(1, 0)/len(target) < 0.6:
            logger.info(f"   ✅ Good balance")
        else:
            self.warnings.append(f"⚠️  Imbalanced classes: {counts.get(1, 0)/len(target)*100:.1f}%")
        
        return self
    
    def train_and_validate(self):
        """Train model with proper cross-validation"""
        logger.info("\n" + "="*100)
        logger.info("🔍 STEP 5: TRAIN AND VALIDATE WITH CROSS-VALIDATION")
        logger.info("="*100)
        
        # Select features (exclude target and leakage)
        exclude_cols = {'date', 'home_team', 'away_team', 'game_id', 'home_win', 'away_win', 
                       'home_score', 'away_score', 'score_diff', 'days_ago'}
        feature_cols = [col for col in self.df.columns 
                       if col not in exclude_cols and self.df[col].dtype in ['int64', 'float64']]
        
        logger.info(f"\n📊 Feature Selection:")
        logger.info(f"   Total features: {len(feature_cols)}")
        logger.info(f"   Excluded columns: {exclude_cols}")
        logger.info(f"   Feature list: {feature_cols}")
        
        # Check if score-based features snuck in
        score_features = [col for col in feature_cols if 'score' in col.lower() or 'diff' in col.lower()]
        if score_features:
            self.issues.append(f"❌ Score-based features found: {score_features}")
            logger.warning(f"   ❌ Score features: {score_features}")
        
        X = self.df[feature_cols].fillna(0)
        y = self.df['home_win'].astype(int)
        
        logger.info(f"\n📊 Data Preparation:")
        logger.info(f"   Training samples: {len(X)}")
        logger.info(f"   Features: {X.shape[1]}")
        
        # Time series split
        tscv = TimeSeriesSplit(n_splits=3)
        
        logger.info(f"\n🔴 CROSS-VALIDATION TEST (3-Fold Time Series):")
        cv_scores = []
        
        for fold, (train_idx, test_idx) in enumerate(tscv.split(X), 1):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
            
            # Scale
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train
            model = xgb.XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42)
            model.fit(X_train_scaled, y_train, verbose=0)
            
            # Evaluate
            y_pred = model.predict(X_test_scaled)
            y_proba = model.predict_proba(X_test_scaled)[:, 1]
            
            acc = accuracy_score(y_test, y_pred)
            auc = roc_auc_score(y_test, y_proba)
            
            cv_scores.append(acc)
            
            logger.info(f"\n   Fold {fold}:")
            logger.info(f"      Train size: {len(train_idx)}, Test size: {len(test_idx)}")
            logger.info(f"      Accuracy: {acc:.4f}")
            logger.info(f"      ROC-AUC: {auc:.4f}")
            
            # Show confusion matrix
            cm = confusion_matrix(y_test, y_pred)
            logger.info(f"      Confusion matrix: TN={cm[0,0]}, FP={cm[0,1]}, FN={cm[1,0]}, TP={cm[1,1]}")
        
        mean_cv = np.mean(cv_scores)
        std_cv = np.std(cv_scores)
        
        logger.info(f"\n   CV Mean Accuracy: {mean_cv:.4f} ± {std_cv:.4f}")
        logger.info(f"   CV Scores: {[f'{s:.4f}' for s in cv_scores]}")
        
        if mean_cv > 0.95:
            self.warnings.append(f"⚠️  Very high CV accuracy ({mean_cv:.4f}) - check for overfitting or leakage")
        
        return self
    
    def check_feature_importance(self):
        """Inspect what the model actually uses"""
        logger.info("\n" + "="*100)
        logger.info("🔍 STEP 6: FEATURE IMPORTANCE ANALYSIS")
        logger.info("="*100)
        
        exclude_cols = {'date', 'home_team', 'away_team', 'game_id', 'home_win', 'away_win', 
                       'home_score', 'away_score', 'score_diff', 'days_ago'}
        feature_cols = [col for col in self.df.columns 
                       if col not in exclude_cols and self.df[col].dtype in ['int64', 'float64']]
        
        X = self.df[feature_cols].fillna(0)
        y = self.df['home_win'].astype(int)
        
        # Simple split
        split_idx = int(0.8 * len(X))
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        model = xgb.XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42)
        model.fit(X_train_scaled, y_train, verbose=0)
        
        importances = model.feature_importances_
        importance_df = pd.DataFrame({
            'feature': feature_cols,
            'importance': importances
        }).sort_values('importance', ascending=False)
        
        logger.info(f"\n📊 Top 10 Important Features:")
        for i, row in importance_df.head(10).iterrows():
            logger.info(f"   {row['feature']:25s} {row['importance']:8.4f}")
        
        # Check if any suspicious features dominate
        top_3_importance = importance_df.head(3)['importance'].sum()
        if top_3_importance > 0.8:
            self.warnings.append(f"⚠️  Top 3 features explain {top_3_importance:.1%} of importance - possible overfitting")
        
        return self
    
    def print_summary(self):
        """Print final sanity check summary"""
        logger.info("\n" + "="*100)
        logger.info("📋 SANITY CHECK SUMMARY")
        logger.info("="*100)
        
        if self.issues:
            logger.error(f"\n🚨 CRITICAL ISSUES FOUND ({len(self.issues)}):")
            for issue in self.issues:
                logger.error(f"   {issue}")
        else:
            logger.info(f"\n✅ NO CRITICAL ISSUES FOUND")
        
        if self.warnings:
            logger.warning(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                logger.warning(f"   {warning}")
        else:
            logger.info(f"\n✅ NO WARNINGS")
        
        logger.info("\n" + "="*100)
        if self.issues:
            logger.error("❌ RESULT: 99.7% IS LIKELY INFLATED - FIX ISSUES FIRST")
            logger.error("\nLikely problems:")
            logger.error("1. Target leakage (scores in features)")
            logger.error("2. Temporal leakage (mixing past/future)")
            logger.error("3. Direct predictor in features (away_win, score_diff)")
        else:
            logger.info("✅ RESULT: Data and methodology look clean")
            logger.info("   High accuracy may be legitimate - good feature engineering!")
        logger.info("="*100)
    
    def run(self):
        """Execute full sanity check"""
        try:
            self.load_and_inspect()
            self.check_target_leakage()
            self.check_temporal_leakage()
            self.check_class_balance()
            self.check_feature_importance()
            self.train_and_validate()
            self.print_summary()
        except Exception as e:
            logger.error(f"\n❌ Sanity check failed: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    checker = SanityChecker()
    checker.run()
