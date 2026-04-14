"""
Trustworthy Decision Agent with RAG - Enhanced decision-making with explanations.

Integrates:
- ML predictions
- Financial analysis
- RAG-based explanations
- Citation tracking
- Confidence scoring
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

from agents.rag_agent import RAGAgent, ExplanationWithCitations


@dataclass
class TrustworthyDecision:
    """A decision with supporting evidence and citations."""
    decision: str
    recommendation: str
    confidence_level: str  # 'high', 'medium', 'low'
    confidence_score: float
    explanation: ExplanationWithCitations
    financial_analysis: Dict
    prediction_analysis: Dict
    risk_assessment: str


class TrustworthyDecisionAgent:
    """
    Enhanced decision agent that provides trustworthy recommendations
    backed by financial knowledge and sources.
    """
    
    def __init__(self, rag_agent: Optional[RAGAgent] = None):
        """
        Initialize trustworthy decision agent.
        
        Args:
            rag_agent: RAG agent for explanations (creates default if None)
        """
        self.logger = logging.getLogger("TrustworthyDecisionAgent")
        self.rag_agent = rag_agent or RAGAgent()
    
    def make_trustworthy_decision(self, prediction: Dict, 
                                 user_data: Dict) -> TrustworthyDecision:
        """
        Make a refinancing decision with full transparency.
        
        Args:
            prediction: Prediction result with confidence
            user_data: User mortgage and financial data
            
        Returns:
            TrustworthyDecision with explanations and citations
        """
        # Extract financial analysis from prediction
        financial_analysis = prediction.get('financial_analysis', {})
        direction = prediction.get('predictions', {}).get('predicted_direction', 'STABLE')
        confidence = prediction.get('reliability', {}).get('overall_reliability', 0.5)
        
        # Perform financial analysis
        decision = self._determine_decision(financial_analysis, direction, confidence)
        confidence_level = self._get_confidence_level(confidence)
        
        # Generate explanation with RAG
        explanation = self.rag_agent.explain_decision(
            {'decision': decision},
            financial_analysis,
            user_data
        )
        
        # Assess risk
        risk_assessment = self._assess_risk(financial_analysis, direction)
        
        # Create prediction analysis summary
        prediction_analysis = {
            'direction': direction,
            'confidence': f"{confidence*100:.0f}%",
            'average_rate_30d': prediction.get('predictions', {}).get('predicted_average_30d'),
            'rate_range': f"{prediction.get('predictions', {}).get('min_rate')} - {prediction.get('predictions', {}).get('max_rate')}"
        }
        
        # Get recommendation text
        recommendation = self._get_recommendation_text(
            decision, 
            financial_analysis, 
            direction,
            confidence
        )
        
        return TrustworthyDecision(
            decision=decision,
            recommendation=recommendation,
            confidence_level=confidence_level,
            confidence_score=explanation.confidence_score,
            explanation=explanation,
            financial_analysis=financial_analysis,
            prediction_analysis=prediction_analysis,
            risk_assessment=risk_assessment
        )
    
    def _determine_decision(self, financial_analysis: Dict, 
                           direction: str, confidence: float) -> str:
        """Determine refinancing decision based on analysis."""
        is_safe = financial_analysis.get('is_financially_safe', False)
        breakeven = financial_analysis.get('breakeven_months', 999)
        remaining_months = financial_analysis.get('remaining_loan_term_months', 0)
        savings = financial_analysis.get('potential_monthly_saving', 0)
        
        # Decision logic with financial rigor
        if not is_safe:
            return "DO NOT REFINANCE"
        
        if direction == "UP":
            if confidence > 0.75:
                return "REFINANCE IMMEDIATELY"
            else:
                return "REFINANCE SOON"
        
        elif direction == "DOWN":
            if breakeven < 12 and confidence > 0.7:
                return "REFINANCE NOW"
            elif breakeven < 24 and confidence > 0.6:
                return "WAIT 1-2 WEEKS"
            elif breakeven < 36 and savings > 100:
                return "MONITOR"
            else:
                return "MONITOR"
        
        else:  # STABLE
            if breakeven < 12 and savings > 150:
                return "MONITOR"
            else:
                return "MONITOR"
    
    def _get_confidence_level(self, confidence_score: float) -> str:
        """Convert numerical confidence to text level."""
        if confidence_score >= 0.75:
            return "high"
        elif confidence_score >= 0.55:
            return "medium"
        else:
            return "low"
    
    def _assess_risk(self, financial_analysis: Dict, direction: str) -> str:
        """Assess risk of refinancing."""
        breakeven = financial_analysis.get('breakeven_months', 999)
        remaining_months = financial_analysis.get('remaining_loan_term_months', 0)
        is_safe = financial_analysis.get('is_financially_safe', False)
        
        risks = []
        
        if not is_safe:
            risks.append("⚠️ Not financially safe relative to remaining loan term")
        
        if breakeven > 36:
            risks.append("⚠️ Long break-even period (may not recover costs if selling sooner)")
        
        if direction == "UP":
            risks.append("⚠️ Rates rising - window may close quickly")
        
        if remaining_months < breakeven:
            risks.append("[WARNING] Loan will be paid off before break-even point")
        
        if not risks:
            return "[OK] Low risk - Financial metrics support refinancing"
        
        risk_text = "\n".join(risks)
        return f"[WARNING] Moderate risks identified:\n{risk_text}"
    
    def _get_recommendation_text(self, decision: str, 
                                financial_analysis: Dict,
                                direction: str,
                                confidence: float) -> str:
        """Get friendly recommendation text."""
        savings = financial_analysis.get('potential_monthly_saving', 0)
        breakeven = financial_analysis.get('breakeven_months', 0)
        
        recommendations = {
            'REFINANCE NOW': (
                f"Strong opportunity to refinance. You could save ${savings:.0f}/month with a {breakeven}-month break-even. "
                f"Rates are favorable and the financial case is compelling. Contact lenders today for quotes."
            ),
            'REFINANCE IMMEDIATELY': (
                f"Rates are rising - refinance now to lock in current rates. Potential savings: ${savings:.0f}/month. "
                f"Waiting could cost you more. Act within 24-48 hours for best rates."
            ),
            'REFINANCE SOON': (
                f"Good opportunity coming. Monitor rates over the next week. With potential savings of ${savings:.0f}/month "
                f"and {breakeven}-month break-even, refinancing looks promising. Plan to refinance within 1-2 weeks."
            ),
            'WAIT 1-2 WEEKS': (
                f"Wait 1-2 weeks for potentially better rates. Current potential savings are ${savings:.0f}/month with "
                f"{breakeven}-month break-even, but rates may decline further. Revisit analysis in 7-14 days."
            ),
            'MONITOR': (
                f"Monitor the market closely. Refinancing isn't urgent right now, but watch for rate movements. "
                f"You could save ${savings:.0f}/month if rates drop an additional 0.25-0.5%."
            ),
            'DO NOT REFINANCE': (
                f"Not recommended at this time. The financial case doesn't support refinancing given your remaining "
                f"loan term and current costs. Revisit if your circumstances change."
            )
        }
        
        return recommendations.get(decision, "Unable to determine recommendation at this time.")
    
    def get_full_report(self, decision: TrustworthyDecision) -> str:
        """Generate a full decision report with all details."""
        report = []
        
        report.append("="*70)
        report.append("TRUSTWORTHY REFINANCING DECISION REPORT")
        report.append("="*70)
        
        # Decision section
        report.append(f"\nDECISION: {decision.decision}")
        report.append(f"Confidence: {decision.confidence_score*100:.0f}% ({decision.confidence_level.upper()})")
        
        # Recommendation
        report.append(f"\nRECOMMENDATION:")
        report.append(f"{decision.recommendation}")
        
        # Explanation
        report.append(f"\nEXPLANATION:")
        report.append(f"{decision.explanation.explanation}")
        
        # Financial Analysis
        report.append(f"\nFINANCIAL ANALYSIS:")
        report.append(f"  Current Rate: {decision.financial_analysis.get('current_rate', 'N/A')}%")
        report.append(f"  Monthly Savings: ${decision.financial_analysis.get('potential_monthly_saving', 0):.2f}")
        report.append(f"  Break-even: {decision.financial_analysis.get('breakeven_months', 'N/A')} months")
        report.append(f"  Remaining Term: {decision.financial_analysis.get('remaining_loan_term_months', 'N/A')} months")
        report.append(f"  Closing Costs: ${decision.financial_analysis.get('estimated_closing_costs', 0):.2f}")
        report.append(f"  Financially Safe: {'Yes [OK]' if decision.financial_analysis.get('is_financially_safe') else 'No [RISK]'}")
        
        # Prediction Analysis
        report.append(f"\nPREDICTION ANALYSIS:")
        report.append(f"  Direction: {decision.prediction_analysis.get('direction', 'STABLE').upper()}")
        report.append(f"  Model Confidence: {decision.prediction_analysis.get('confidence', 'N/A')}")
        report.append(f"  Average Rate (30d): {decision.prediction_analysis.get('average_rate_30d', 'N/A')}%")
        
        # Risk Assessment
        report.append(f"\nRISK ASSESSMENT:")
        report.append(f"{decision.risk_assessment}")
        
        # Sources
        report.append(f"\nSOURCES & CITATIONS:")
        for i, citation in enumerate(decision.explanation.citations, 1):
            report.append(f"\n{i}. {citation.title}")
            report.append(f"   Source: {citation.source}")
            report.append(f"   Relevance: {citation.relevance_score:.0%}")
            report.append(f"   Key insight: {citation.quote}")
        
        report.append("\n" + "="*70)
        
        return "\n".join(report)


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    agent = TrustworthyDecisionAgent()
    
    # Sample prediction with financial analysis
    sample_prediction = {
        'predictions': {
            'predicted_direction': 'DOWN',
            'predicted_average_30d': 4.0,
            'min_rate': 3.9,
            'max_rate': 4.1
        },
        'reliability': {'overall_reliability': 0.82},
        'financial_analysis': {
            'current_rate': 4.5,
            'potential_monthly_saving': 200,
            'estimated_closing_costs': 5000,
            'breakeven_months': 25,
            'remaining_loan_term_months': 180,
            'is_financially_safe': True,
            'credit_score': 750
        }
    }
    
    sample_user = {
        'id': 'USER-001',
        'name': 'John Doe',
        'credit_score': 750
    }
    
    # Make decision
    decision = agent.make_trustworthy_decision(sample_prediction, sample_user)
    
    # Print full report
    print(agent.get_full_report(decision))
