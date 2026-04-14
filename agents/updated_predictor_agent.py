"""
Updated Predictor Agent that uses ML models from HuggingFace Hub.

This agent:
- Loads trained ARIMA/Prophet models from HuggingFace
- Makes rate predictions using ensemble approach
- Provides confidence intervals
- Returns actionable forecasts
"""

from models.predictor import MortgageRatePredictor
from typing import Dict
import json


class PredictorAgent:
    """ML-powered rate prediction agent."""
    
    def __init__(self):
        """Initialize with models from HuggingFace Hub."""
        self.predictor = MortgageRatePredictor(model_type='best')
        self.name = "Predictor Agent"
    
    def predict_rates(self, market_data: Dict) -> Dict:
        """
        Predict mortgage rate movements.
        
        Args:
            market_data: Dict with 'current_rate' and optional 'history'
            
        Returns:
            Dict with predictions and analysis
        """
        current_rate = market_data.get('current_rate', 4.5)
        
        print(f"\n🤖 {self.name}: Analyzing rate trends...")
        
        # Get ML prediction
        prediction = self.predictor.predict(
            current_rate=current_rate,
            steps=30
        )
        
        analysis = {
            'agent': self.name,
            'current_rate': prediction['current_rate'],
            'predicted_direction': prediction['predicted_direction'],
            'predicted_average_30d': prediction['predicted_average'],
            'confidence': prediction['confidence'],
            'forecast_data': {
                'min': prediction['predicted_min'],
                'max': prediction['predicted_max'],
                'range': prediction['predicted_max'] - prediction['predicted_min']
            },
            'raw_forecast': prediction['forecast'],
            'reasoning': self._generate_reasoning(prediction)
        }
        
        print(f"   ✅ Prediction: {prediction['predicted_direction']}")
        print(f"   📊 Avg 30-day rate: {prediction['predicted_average']:.2f}%")
        print(f"   🎯 Confidence: {prediction['confidence']*100:.0f}%")
        
        return analysis
    
    def _generate_reasoning(self, prediction: Dict) -> str:
        """Generate human-readable reasoning."""
        direction = prediction['predicted_direction']
        current = prediction['current_rate']
        avg_future = prediction['predicted_average']
        change = avg_future - current
        
        if direction == "DOWN":
            return (f"Rates predicted to drop by {abs(change):.2f}% over 30 days. "
                   f"Current: {current}% → Predicted avg: {avg_future:.2f}%")
        elif direction == "UP":
            return (f"Rates predicted to rise by {change:.2f}% over 30 days. "
                   f"Current: {current}% → Predicted avg: {avg_future:.2f}%")
        else:
            return (f"Rates predicted to remain stable. "
                   f"Current: {current}% ≈ Predicted avg: {avg_future:.2f}%")
    
    def get_prediction_reliability(self, prediction: Dict) -> Dict:
        """
        Assess prediction reliability.
        
        Returns:
            Dict with reliability metrics
        """
        forecast = prediction['forecast_data']
        confidence = prediction['confidence']
        
        # Narrow range = more reliable
        range_score = 1 - min(forecast['range'] / 2, 1.0)
        
        # High confidence = more reliable
        confidence_score = confidence
        
        # Overall reliability
        reliability = (range_score + confidence_score) / 2
        
        return {
            'overall_reliability': reliability,
            'confidence_score': confidence_score,
            'range_score': range_score,
            'reliability_level': self._reliability_level(reliability)
        }
    
    @staticmethod
    def _reliability_level(score: float) -> str:
        """Map score to reliability level."""
        if score > 0.8:
            return "VERY HIGH"
        elif score > 0.6:
            return "HIGH"
        elif score > 0.4:
            return "MODERATE"
        else:
            return "LOW"


class DecisionAgent:
    """Uses predictions to make refinancing decisions."""
    
    def __init__(self):
        self.name = "Decision Agent"
        self.predictor_agent = PredictorAgent()
    
    def make_decision(self, user_data: Dict, market_data: Dict) -> Dict:
        """
        Make refinancing decision based on predictions and user data.
        
        Args:
            user_data: User's current mortgage details
            market_data: Current market rate information
            
        Returns:
            Dict with decision and reasoning
        """
        print(f"\n🤖 {self.name}: Making refinancing decision...")
        
        # Get predictions
        predictions = self.predictor_agent.predict_rates(market_data)
        reliability = self.predictor_agent.get_prediction_reliability(predictions)
        
        # Calculate breakeven
        current_rate = user_data.get('current_rate', 4.5)
        market_rate = market_data.get('current_rate', 4.2)
        loan_term_years = user_data.get('loan_term_years', 30)
        monthly_payment = user_data.get('monthly_payment', 1200)
        
        # Estimate breakeven months
        monthly_saving = monthly_payment * (current_rate - market_rate) / 100 / 12
        closing_costs = user_data.get('closing_costs', 5000)
        breakeven_months = closing_costs / monthly_saving if monthly_saving > 0 else float('inf')
        
        is_safe = breakeven_months < (loan_term_years * 12 * 0.75)  # Less than 75% of remaining term
        
        # Make decision
        decision = self._determine_action(
            predictions, 
            reliability,
            is_safe,
            breakeven_months
        )
        
        result = {
            'agent': self.name,
            'decision': decision,
            'predictions': predictions,
            'reliability': reliability,
            'financial_analysis': {
                'current_rate': current_rate,
                'market_rate': market_rate,
                'potential_monthly_saving': monthly_saving,
                'estimated_closing_costs': closing_costs,
                'breakeven_months': breakeven_months,
                'is_financially_safe': is_safe,
                'remaining_loan_term_months': loan_term_years * 12
            },
            'confidence_level': self._confidence_level(reliability, is_safe)
        }
        
        print(f"   ✅ Decision: {decision}")
        print(f"   💰 Monthly savings: ${monthly_saving:.2f}")
        print(f"   ⏱️  Breakeven: {breakeven_months:.1f} months")
        
        return result
    
    def _determine_action(self, predictions: Dict, reliability: Dict, 
                         is_safe: bool, breakeven_months: float) -> str:
        """Determine action based on analysis."""
        direction = predictions['predicted_direction']
        confidence = reliability['overall_reliability']
        
        if not is_safe:
            return "DO NOT REFINANCE - Not financially safe for remaining loan term"
        
        if direction == "DOWN" and breakeven_months < 24:
            if confidence > 0.75:
                return "REFINANCE NOW - Strong prediction of rate drops with safe breakeven"
            else:
                return "REFINANCE CAUTIOUSLY - Rates declining but lower confidence"
        elif direction == "UP":
            if confidence > 0.75:
                return "REFINANCE IMMEDIATELY - Rates predicted to rise, act now"
            else:
                return "REFINANCE SOON - Rates likely rising, moderate confidence"
        elif direction == "DOWN" and breakeven_months < 36:
            return "WAIT 1-2 WEEKS - Rates dropping, better terms coming soon"
        else:
            return "MONITOR - No strong signal, continue monitoring market"
    
    @staticmethod
    def _confidence_level(reliability: Dict, is_safe: bool) -> str:
        """Determine overall confidence."""
        if not is_safe:
            return "CAUTION"
        
        score = reliability['overall_reliability']
        if score > 0.85:
            return "HIGH CONFIDENCE"
        elif score > 0.7:
            return "MODERATE-HIGH CONFIDENCE"
        elif score > 0.5:
            return "MODERATE CONFIDENCE"
        else:
            return "LOW CONFIDENCE"


# Example Usage

if __name__ == "__main__":
    # User data
    user_data = {
        'current_rate': 4.5,
        'loan_term_years': 15,
        'monthly_payment': 1200,
        'closing_costs': 5000
    }
    
    # Market data
    market_data = {
        'current_rate': 4.2,
        'source': 'FRED API'
    }
    
    # Make decision
    decision_agent = DecisionAgent()
    result = decision_agent.make_decision(user_data, market_data)
    
    print("\n" + "="*70)
    print("DECISION SUMMARY")
    print("="*70)
    print(f"🎯 Recommendation: {result['decision']}")
    print(f"📊 Confidence: {result['confidence_level']}")
    print(f"💰 Potential savings: ${result['financial_analysis']['potential_monthly_saving']:.2f}/month")
    print("="*70)
