"""
RAG Integration Layer - Coordinates orchestration with RAG explanations.

Bridges:
- Orchestration engine
- Decision agent
- RAG agent
- Notification system
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging
import json
from datetime import datetime

from agents.trustworthy_decision_agent import TrustworthyDecisionAgent, Trustworthy Decision
from agents.rag_agent import ExplanationWithCitations
from agents.knowledge_base import KnowledgeBase


@dataclass
class RichNotification:
    """A notification with trustworthy decision and citations."""
    user_id: str
    user_name: str
    subject: str
    decision: str
    recommendation: str
    confidence_score: float
    explanation: str
    citations: List[Dict]
    financial_summary: Dict
    risk_assessment: str
    call_to_action: str
    timestamp: str


class RAGOrchestrationIntegration:
    """
    Integrates RAG-powered explanations into the orchestration pipeline.
    """
    
    def __init__(self, trustworthy_agent: Optional[TrustworthyDecisionAgent] = None):
        """
        Initialize RAG integration.
        
        Args:
            trustworthy_agent: TrustworthyDecisionAgent (creates default if None)
        """
        self.logger = logging.getLogger("RAGOrchestrationIntegration")
        self.trustworthy_agent = trustworthy_agent or TrustworthyDecisionAgent()
        self.knowledge_base = self.trustworthy_agent.rag_agent.kb
    
    def create_rich_notification(self, user_id: str, user_name: str, 
                                prediction: Dict, 
                                user_data: Dict) -> RichNotification:
        """
        Create a notification with trustworthy decision and citations.
        
        Args:
            user_id: User identifier
            user_name: User's name for personalization
            prediction: Prediction result from ML pipeline
            user_data: User's mortgage and financial information
            
        Returns:
            RichNotification with full decision details and sources
        """
        
        # Get trustworthy decision with RAG explanations
        decision = self.trustworthy_agent.make_trustworthy_decision(
            prediction, 
            user_data
        )
        
        # Format citations for notification
        citations = self._format_citations_for_notification(
            decision.explanation.citations
        )
        
        # Create call to action
        call_to_action = self._get_call_to_action(
            decision.decision,
            decision.confidence_score
        )
        
        # Create subject line
        subject = self._create_subject_line(
            decision.decision,
            decision.confidence_level
        )
        
        # Create rich notification
        notification = RichNotification(
            user_id=user_id,
            user_name=user_name,
            subject=subject,
            decision=decision.decision,
            recommendation=decision.recommendation,
            confidence_score=decision.confidence_score,
            explanation=decision.explanation.explanation,
            citations=citations,
            financial_summary=self._create_financial_summary(decision),
            risk_assessment=decision.risk_assessment,
            call_to_action=call_to_action,
            timestamp=datetime.now().isoformat()
        )
        
        return notification
    
    def _format_citations_for_notification(self, citations: list) -> List[Dict]:
        """Format citations for user-friendly display in notifications."""
        formatted = []
        
        for i, citation in enumerate(citations, 1):
            formatted.append({
                'number': i,
                'title': citation.title,
                'source': citation.source,
                'relevance': f"{citation.relevance_score*100:.0f}%",
                'quote': citation.quote,
                'relevance_text': self._relevance_to_text(citation.relevance_score)
            })
        
        return formatted
    
    def _relevance_to_text(self, score: float) -> str:
        """Convert relevance score to readable text."""
        if score >= 0.8:
            return "Highly relevant"
        elif score >= 0.6:
            return "Relevant"
        else:
            return "Moderately relevant"
    
    def _create_financial_summary(self, decision: Trustworthy Decision) -> Dict:
        """Create a concise financial summary for notification."""
        return {
            'monthly_savings': f"${decision.financial_analysis.get('potential_monthly_saving', 0):.2f}",
            'breakeven_months': decision.financial_analysis.get('breakeven_months', 'N/A'),
            'remaining_term': decision.financial_analysis.get('remaining_loan_term_months', 'N/A'),
            'closing_costs': f"${decision.financial_analysis.get('estimated_closing_costs', 0):.2f}",
            'rate_direction': decision.prediction_analysis.get('direction', 'STABLE'),
            'predicted_rate': decision.prediction_analysis.get('average_rate_30d', 'N/A')
        }
    
    def _get_call_to_action(self, decision: str, confidence: float) -> str:
        """Get action-oriented call to action based on decision."""
        
        ctas = {
            'REFINANCE NOW': (
                "📞 Contact lenders today for rate quotes\n"
                "⏱️ Act within 24 hours before rates change\n"
                "📋 Have your financial documents ready"
            ),
            'REFINANCE IMMEDIATELY': (
                "🚨 Call lenders immediately - rates are rising\n"
                "⏱️ Get quotes within 24 hours\n"
                "📋 Lock in rates today"
            ),
            'REFINANCE SOON': (
                "📞 Contact lenders within 1 week\n"
                "⏰ Set a reminder to compare rates\n"
                "📋 Request no-obligation quotes"
            ),
            'WAIT 1-2 WEEKS': (
                "📅 Set a reminder to check rates in 7-14 days\n"
                "📊 Monitor your local market\n"
                "📋 Prepare documents for when you're ready"
            ),
            'MONITOR': (
                "👀 Check rates weekly\n"
                "📊 Watch for 0.25% rate decline\n"
                "⏰ We'll alert you when conditions improve"
            ),
            'DO NOT REFINANCE': (
                "💭 Revisit this analysis in 3-6 months\n"
                "📊 Monitor rate trends\n"
                "📞 Contact us if your situation changes"
            )
        }
        
        return ctas.get(decision, "Contact your lender for more information")
    
    def _create_subject_line(self, decision: str, confidence_level: str) -> str:
        """Create an engaging subject line."""
        
        subjects = {
            'REFINANCE NOW': "🎯 Strong Opportunity: Refinance Now to Save Money",
            'REFINANCE IMMEDIATELY': "🚨 Urgent: Rates Rising - Refinance Today",
            'REFINANCE SOON': "✨ Good Opportunity: Plan to Refinance This Week",
            'WAIT 1-2 WEEKS': "📈 Opportunity Coming: Rates May Drop Soon",
            'MONITOR': "📊 Rates Stabilizing: Keep an Eye Out",
            'DO NOT REFINANCE': "📌 Refinancing Not Recommended At This Time"
        }
        
        return subjects.get(decision, "Mortgage Rate Update & Analysis")
    
    def create_email_html(self, notification: RichNotification) -> str:
        """Create professional HTML email from notification."""
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px; text-align: center; margin-bottom: 30px; }}
        .section {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #667eea; }}
        .decision {{ font-size: 24px; font-weight: bold; color: #667eea; margin-bottom: 10px; }}
        .recommendation {{ background: white; padding: 15px; border-radius: 5px; margin-bottom: 15px; }}
        .confidence {{ display: inline-block; background: #667eea; color: white; padding: 8px 12px; border-radius: 5px; font-weight: bold; }}
        .citations {{ background: white; padding: 15px; border-radius: 5px; }}
        .citation-item {{ margin-bottom: 15px; padding: 12px; background: #f8f9fa; border-left: 3px solid #667eea; }}
        .citation-title {{ font-weight: bold; color: #333; }}
        .citation-quote {{ font-style: italic; color: #666; margin-top: 8px; }}
        .cta-button {{ display: inline-block; background: #667eea; color: white; padding: 12px 24px; border-radius: 5px; text-decoration: none; font-weight: bold; margin-top: 10px; }}
        .footer {{ color: #999; font-size: 12px; text-align: center; margin-top: 30px; border-top: 1px solid #ddd; padding-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Mortgage Rate Update for {notification.user_name}</h1>
            <p>Personalized Analysis with Sources</p>
        </div>
        
        <div class="section">
            <div class="decision">{notification.decision}</div>
            <span class="confidence">Confidence: {notification.confidence_score*100:.0f}%</span>
            <div class="recommendation">
                <p>{notification.recommendation}</p>
            </div>
        </div>
        
        <div class="section">
            <h3>📊 Financial Summary</h3>
            <ul>
                <li><strong>Potential Monthly Savings:</strong> {notification.financial_summary['monthly_savings']}</li>
                <li><strong>Break-even Period:</strong> {notification.financial_summary['breakeven_months']} months</li>
                <li><strong>Closing Costs:</strong> {notification.financial_summary['closing_costs']}</li>
                <li><strong>Loan Remaining:</strong> {notification.financial_summary['remaining_term']} months</li>
                <li><strong>Rate Direction:</strong> {notification.financial_summary['rate_direction']}</li>
            </ul>
        </div>
        
        <div class="section">
            <h3>💡 Analysis</h3>
            <p>{notification.explanation}</p>
        </div>
        
        <div class="section">
            <h3>⚠️ Risk Assessment</h3>
            <p>{notification.risk_assessment}</p>
        </div>
        
        <div class="section">
            <h3>📚 Sources & Citations</h3>
            <div class="citations">"""
        
        for citation in notification.citations:
            html += f"""
                <div class="citation-item">
                    <div class="citation-title">{citation['number']}. {citation['title']}</div>
                    <div style="color: #999; font-size: 12px; margin-top: 5px;">
                        Source: {citation['source']} · Relevance: {citation['relevance']}
                    </div>
                    <div class="citation-quote">"{citation['quote']}"</div>
                </div>"""
        
        html += f"""
            </div>
        </div>
        
        <div class="section">
            <h3>🎯 Next Steps</h3>
            <p>{notification.call_to_action.replace(chr(10), '<br>')}</p>
        </div>
        
        <div class="footer">
            <p>This analysis is provided by your Mortgage Rate Notifier system.</p>
            <p>Generated: {notification.timestamp}</p>
            <p>User ID: {notification.user_id}</p>
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def create_email_text(self, notification: RichNotification) -> str:
        """Create plain text email from notification."""
        
        text = f"""MORTGAGE RATE UPDATE FOR {notification.user_name}

DECISION: {notification.decision}
Confidence: {notification.confidence_score*100:.0f}%

RECOMMENDATION:
{notification.recommendation}

FINANCIAL SUMMARY:
- Monthly Savings: {notification.financial_summary['monthly_savings']}
- Break-even: {notification.financial_summary['breakeven_months']} months
- Closing Costs: {notification.financial_summary['closing_costs']}
- Remaining Loan Term: {notification.financial_summary['remaining_term']} months
- Predicted Rate: {notification.financial_summary['predicted_rate']}%

ANALYSIS:
{notification.explanation}

RISK ASSESSMENT:
{notification.risk_assessment}

SOURCES & CITATIONS:
"""
        
        for citation in notification.citations:
            text += f"""
{citation['number']}. {citation['title']}
   Source: {citation['source']}
   Relevance: {citation['relevance']}
   "{citation['quote']}"
"""
        
        text += f"""
NEXT STEPS:
{notification.call_to_action}

Generated: {notification.timestamp}
"""
        
        return text
    
    def save_notification_to_file(self, notification: RichNotification, 
                                 directory: str = "notifications") -> str:
        """Save notification to JSON file for audit trail."""
        import os
        
        os.makedirs(directory, exist_ok=True)
        
        filename = f"{directory}/{notification.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                'user_id': notification.user_id,
                'user_name': notification.user_name,
                'subject': notification.subject,
                'decision': notification.decision,
                'recommendation': notification.recommendation,
                'confidence_score': notification.confidence_score,
                'explanation': notification.explanation,
                'citations': notification.citations,
                'financial_summary': notification.financial_summary,
                'risk_assessment': notification.risk_assessment,
                'call_to_action': notification.call_to_action,
                'timestamp': notification.timestamp
            }, f, indent=2)
        
        self.logger.info(f"Notification saved: {filename}")
        return filename


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    integration = RAGOrchestrationIntegration()
    
    # Sample data
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
        'name': 'Sarah Johnson',
        'credit_score': 750
    }
    
    # Create rich notification
    notification = integration.create_rich_notification(
        user_id=sample_user['id'],
        user_name=sample_user['name'],
        prediction=sample_prediction,
        user_data=sample_user
    )
    
    # Print summary
    print("="*70)
    print("NOTIFICATION PREVIEW")
    print("="*70)
    print(f"\nSubject: {notification.subject}")
    print(f"Decision: {notification.decision} (Confidence: {notification.confidence_score*100:.0f}%)")
    print(f"\nRecommendation:\n{notification.recommendation}")
    print(f"\nCitations: {len(notification.citations)} sources")
    
    # Save notification
    notification.save_notification_to_file(notification)
    
    # Example email generation
    print("\n" + "="*70)
    print("EMAIL HTML (first 500 chars):")
    html = integration.create_email_html(notification)
    print(html[:500] + "...")
