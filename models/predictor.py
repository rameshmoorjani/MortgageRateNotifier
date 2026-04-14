"""
Integration guide for MortgageRateNotifier + MortgageRateML models.

This document explains how to integrate trained models from HuggingFace Hub
into the MortgageRateNotifier system.

Date: April 8, 2026
Status: Ready for implementation
"""

# MortgageRateNotifier Integration Guide

## Overview

The trained models from MortgageRateML are now published to:
**https://huggingface.co/rameshb79/mortgage-rate-predictor**

These models will be integrated into MortgageRateNotifier as the **prediction engine**.

## Architecture

```
┌─────────────────────────────────────────┐
│   User Request                          │
│   (Should I refinance?)                 │
└────────────────┬────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│   Orchestrator Agent                    │
│   (Coordinates workflow)                │
└────────────────┬────────────────────────┘
    ↓        ↓        ↓         ↓
 Data    Market   Predict    Risk
 Agent   Analysis  Agent     Agent
         Agent
         
         ↓
    Uses Models from HuggingFace Hub:
    - ARIMA Model (arima_best.pkl)
    - Prophet Model (prophet_best.pkl)
```

## Integration Steps

### Step 1: Add Model Loader Class

Create `models/predictor.py`:

```python
from huggingface_hub import hf_hub_download
import joblib
import os
import pandas as pd
import numpy as np
from typing import Dict, Tuple


class MortgageRatePredictor:
    """Load and use trained models from HuggingFace Hub."""
    
    REPO_ID = "rameshb79/mortgage-rate-predictor"
    
    def __init__(self, model_type: str = 'best', cache_dir: str = 'models/'):
        """
        Initialize predictor with models from HuggingFace.
        
        Args:
            model_type: 'arima', 'prophet', or 'best' (default)
            cache_dir: Local directory to cache downloaded models
        """
        self.model_type = model_type
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        self.arima_model = None
        self.prophet_model = None
        
        self._load_models()
    
    def _load_models(self):
        """Download and load models from HuggingFace Hub."""
        try:
            print("📥 Loading models from HuggingFace Hub...")
            
            # Download ARIMA model
            arima_path = hf_hub_download(
                repo_id=self.REPO_ID,
                filename="arima_best.pkl",
                cache_dir=self.cache_dir
            )
            self.arima_model = joblib.load(arima_path)
            print("✅ ARIMA model loaded")
            
            # Download Prophet model
            prophet_path = hf_hub_download(
                repo_id=self.REPO_ID,
                filename="prophet_best.pkl",
                cache_dir=self.cache_dir
            )
            self.prophet_model = joblib.load(prophet_path)
            print("✅ Prophet model loaded")
            
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            print("   Make sure HuggingFace Hub repo exists and is public")
            raise
    
    def predict_arima(self, steps: int = 30) -> Dict:
        """
        Get ARIMA forecast.
        
        Args:
            steps: Number of periods to forecast
            
        Returns:
            Dict with forecast and metadata
        """
        forecast = self.arima_model.get_forecast(steps=steps)
        forecast_df = forecast.summary_frame()
        
        return {
            'model': 'ARIMA',
            'forecast': forecast_df['mean'].values,
            'confidence_interval_lower': forecast_df['mean_ci_lower'].values,
            'confidence_interval_upper': forecast_df['mean_ci_upper'].values,
            'next_7_days': forecast_df['mean'].values[:7].mean(),
            'next_30_days': forecast_df['mean'].values[:30].mean(),
        }
    
    def predict_prophet(self, steps: int = 30) -> Dict:
        """
        Get Prophet forecast.
        
        Args:
            steps: Number of periods to forecast
            
        Returns:
            Dict with forecast and metadata
        """
        future = self.prophet_model.make_future_dataframe(periods=steps)
        forecast = self.prophet_model.predict(future)
        
        # Get only future predictions
        future_forecast = forecast.tail(steps)
        
        return {
            'model': 'Prophet',
            'forecast': future_forecast['yhat'].values,
            'confidence_interval_lower': future_forecast['yhat_lower'].values,
            'confidence_interval_upper': future_forecast['yhat_upper'].values,
            'next_7_days': future_forecast['yhat'].values[:7].mean(),
            'next_30_days': future_forecast['yhat'].values[:30].mean(),
        }
    
    def predict_ensemble(self, steps: int = 30) -> Dict:
        """
        Average predictions from both models.
        
        Args:
            steps: Number of periods to forecast
            
        Returns:
            Dict with ensemble forecast
        """
        arima_pred = self.predict_arima(steps)
        prophet_pred = self.predict_prophet(steps)
        
        # Average the predictions
        ensemble_forecast = (arima_pred['forecast'] + prophet_pred['forecast']) / 2
        ensemble_ci_lower = (arima_pred['confidence_interval_lower'] + 
                            prophet_pred['confidence_interval_lower']) / 2
        ensemble_ci_upper = (arima_pred['confidence_interval_upper'] + 
                            prophet_pred['confidence_interval_upper']) / 2
        
        return {
            'model': 'Ensemble (ARIMA + Prophet)',
            'forecast': ensemble_forecast,
            'confidence_interval_lower': ensemble_ci_lower,
            'confidence_interval_upper': ensemble_ci_upper,
            'next_7_days': ensemble_forecast[:7].mean(),
            'next_30_days': ensemble_forecast[:30].mean(),
            'arima_weight': 0.5,
            'prophet_weight': 0.5,
        }
    
    def predict(self, current_rate: float, steps: int = 30) -> Dict:
        """
        Make prediction and determine recommendation.
        
        Args:
            current_rate: Current mortgage rate (e.g., 4.5)
            steps: Forecast period (default 30 days)
            
        Returns:
            Dict with forecast and recommendation
        """
        # Get ensemble forecast
        forecast = self.predict_ensemble(steps)
        
        # Analyze trend
        pred_values = forecast['forecast']
        avg_future_rate = pred_values.mean()
        min_future_rate = pred_values.min()
        max_future_rate = pred_values.max()
        
        # Determine direction
        if avg_future_rate < current_rate - 0.25:
            direction = "DOWN"
            confidence = 0.85
        elif avg_future_rate > current_rate + 0.25:
            direction = "UP"
            confidence = 0.80
        else:
            direction = "STABLE"
            confidence = 0.70
        
        return {
            'current_rate': current_rate,
            'forecast': forecast,
            'predicted_direction': direction,
            'predicted_average': avg_future_rate,
            'predicted_min': min_future_rate,
            'predicted_max': max_future_rate,
            'confidence': confidence,
            'recommendation': self._generate_recommendation(
                current_rate, direction, avg_future_rate
            )
        }
    
    def _generate_recommendation(self, current_rate: float, 
                                direction: str, avg_future: float) -> str:
        """Generate recommendation based on forecast."""
        if direction == "DOWN" and avg_future < current_rate - 0.5:
            return "WAIT - Rates predicted to drop significantly"
        elif direction == "UP":
            return "REFINANCE NOW - Rates likely to increase"
        elif direction == "DOWN":
            return "GOOD TIME - Wait slightly for better rates"
        else:
            return "MONITOR - Rates stable, no urgency"


# Example Usage

if __name__ == "__main__":
    # Initialize predictor
    predictor = MortgageRatePredictor(model_type='best')
    
    # Make prediction
    result = predictor.predict(current_rate=4.5, steps=30)
    
    print("\n" + "="*70)
    print("MORTGAGE RATE PREDICTION")
    print("="*70)
    print(f"Current Rate: {result['current_rate']}%")
    print(f"Predicted Direction: {result['predicted_direction']}")
    print(f"Predicted Average (30 days): {result['predicted_average']:.2f}%")
    print(f"Predicted Range: {result['predicted_min']:.2f}% - {result['predicted_max']:.2f}%")
    print(f"Confidence: {result['confidence']*100:.0f}%")
    print(f"\n🎯 Recommendation: {result['recommendation']}")
