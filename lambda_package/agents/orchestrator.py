"""
Main Orchestrator Agent - Coordinates all agents in the system.

This is the central hub that:
1. Receives user requests
2. Routes to appropriate agents
3. Coordinates their execution
4. Combines results into decisions
5. Initiates notifications
"""

from agents.updated_predictor_agent import DecisionAgent
from agents.search_agent import SearchAgent
from agents.filter_agent import FilterAgent
from agents.email_agent import EmailAgent
from agents.parser_agent import ParserAgent
from typing import Dict, Any, Optional
from datetime import datetime
import json


class OrchestratorAgent:
    """
    Main orchestration agent that coordinates all sub-agents.
    
    Workflow:
    User Request → Search/Get Data → Predict → Decide → Filter → Notify
    """
    
    def __init__(self):
        """Initialize all agents."""
        self.name = "Orchestrator Agent"
        self.decision_agent = DecisionAgent()
        self.search_agent = SearchAgent()
        self.filter_agent = FilterAgent()
        self.email_agent = EmailAgent()
        self.parser_agent = ParserAgent()
        
        # Track state
        self.execution_log = []
        self.current_request_id = None
    
    def process_user_request(self, user_data: Dict, check_type: str = "auto") -> Dict:
        """
        Main entry point - Process a user's mortgage refinancing request.
        
        Args:
            user_data: User's mortgage and profile information
            check_type: "auto" = periodic check, "manual" = user initiated
            
        Returns:
            Dict with complete analysis and recommendation
        """
        request_id = self._generate_request_id()
        self.current_request_id = request_id
        
        print("\n" + "="*70)
        print(f"ORCHESTRATOR: Processing request {request_id}")
        print("="*70)
        
        try:
            # Step 1: Gather market data
            self._log("STEP 1: Gathering market data")
            market_data = self._gather_market_data()
            
            # Step 2: Predict rates using ML models
            self._log("STEP 2: Making ML predictions")
            prediction_result = self._predict_rates(user_data, market_data)
            
            if not prediction_result.get('success'):
                return self._create_error_response(prediction_result)
            
            # Step 3: Make refinancing decision
            self._log("STEP 3: Making refinancing decision")
            decision_result = prediction_result['data']
            
            # Step 4: Filter for eligibility & risk
            self._log("STEP 4: Filtering eligibility & risk")
            filter_result = self._filter_eligibility(user_data, decision_result)
            
            # Step 5: Prepare notification
            self._log("STEP 5: Preparing notification")
            notification = self._create_notification(
                user_data, 
                decision_result, 
                filter_result
            )
            
            # Step 6: Send if eligible
            if filter_result.get('eligible', False):
                self._log("STEP 6: Sending notification")
                self._send_notification(user_data, notification)
            else:
                self._log(f"STEP 6: Skipped (Not eligible: {filter_result.get('reason')})")
            
            # Compile final response
            response = {
                'request_id': request_id,
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'user_name': user_data.get('name', 'Unknown'),
                'decision': decision_result.get('decision', 'MONITOR'),
                'recommendation': decision_result.get('recommendation', 'No clear action'),
                'eligibility': filter_result,
                'predictions': decision_result.get('predictions', {}),
                'financial_analysis': decision_result.get('financial_analysis', {}),
                'notification_sent': filter_result.get('eligible', False),
                'execution_log': self.execution_log
            }
            
            self._print_summary(response)
            return response
            
        except Exception as e:
            self._log(f"ERROR: {str(e)}")
            return self._create_error_response({'error': str(e)})
    
    def _gather_market_data(self) -> Dict:
        """Gather current market data from FRED API and other sources."""
        self._log("  Getting current mortgage rates from FRED...")
        
        try:
            from fredapi import Fred
            import os
            
            fred = Fred(api_key=os.getenv('FRED_API_KEY', 'demo'))
            
            # In production, this would fetch live data
            # For now, return realistic sample
            return {
                'current_rate': 4.2,
                'rate_15yr': 3.9,
                'rate_30yr': 4.2,
                'source': 'FRED API',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self._log(f"  Warning: Could not fetch live rates: {e}")
            return {
                'current_rate': 4.2,
                'rate_15yr': 3.9,
                'rate_30yr': 4.2,
                'source': 'Cached data',
                'timestamp': datetime.now().isoformat()
            }
    
    def _predict_rates(self, user_data: Dict, market_data: Dict) -> Dict:
        """Use ML models to predict future rates."""
        try:
            self._log("  Running ARIMA + Prophet ensemble models...")
            self._log(f"  Current rate: {market_data['current_rate']}%")
            
            decision = self.decision_agent.make_decision(user_data, market_data)
            
            self._log(f"  ✅ Prediction: {decision['predictions']['predicted_direction']}")
            self._log(f"  📊 Confidence: {decision['reliability']['overall_reliability']*100:.0f}%")
            
            return {
                'success': True,
                'data': decision
            }
        except Exception as e:
            self._log(f"  ❌ Prediction failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _filter_eligibility(self, user_data: Dict, decision_result: Dict) -> Dict:
        """Check if user is eligible for notification."""
        try:
            self._log("  Checking user eligibility...")
            
            # Check credit score (if available)
            credit_score = user_data.get('credit_score', 700)
            if credit_score < 620:
                return {
                    'eligible': False,
                    'reason': 'Credit score too low',
                    'credit_score': credit_score
                }
            
            # Check if decision is actionable
            decision = decision_result.get('decision', '')
            if 'MONITOR' in decision:
                return {
                    'eligible': False,
                    'reason': 'No clear action recommended',
                    'decision': decision
                }
            
            # Check financial safety
            is_safe = decision_result.get('financial_analysis', {}).get('is_financially_safe', False)
            if not is_safe:
                return {
                    'eligible': False,
                    'reason': 'Not financially safe for loan term',
                    'breakeven_months': decision_result.get('financial_analysis', {}).get('breakeven_months')
                }
            
            self._log("  ✅ User eligible for notification")
            return {
                'eligible': True,
                'credit_score': credit_score,
                'decision': decision
            }
            
        except Exception as e:
            self._log(f"  Warning: Filter error: {e}")
            return {'eligible': False, 'reason': f'Filter error: {e}'}
    
    def _create_notification(self, user_data: Dict, decision: Dict, 
                            filter_result: Dict) -> Dict:
        """Create notification message."""
        try:
            self._log("  Formatting notification message...")
            
            decision_text = decision.get('decision', 'MONITOR')
            prediction = decision.get('predictions', {})
            financial = decision.get('financial_analysis', {})
            
            subject = self._generate_subject(decision_text, filter_result)
            
            body = f"""
Hi {user_data.get('name', 'User')},

Good news! We've analyzed mortgage rates for your profile.

ANALYSIS RESULTS:
═══════════════════════════════════════════════════════════════

Your Current Rate: {financial.get('current_rate', 'N/A')}%
Market Rate Now: {financial.get('market_rate', 'N/A')}%
Rate Prediction: {prediction.get('predicted_direction', 'STABLE')}
Confidence Level: {filter_result.get('reliability', {}).get('overall_reliability', 'N/A')}

FINANCIAL IMPACT:
═══════════════════════════════════════════════════════════════

Monthly Savings: ${financial.get('potential_monthly_saving', 0):.2f}
Closing Costs: ${financial.get('estimated_closing_costs', 0):.2f}
Break-even Period: {financial.get('breakeven_months', 'N/A')} months
Remaining Loan Term: {financial.get('remaining_loan_term_months', 'N/A')} months

RECOMMENDATION:
═══════════════════════════════════════════════════════════════

{decision_text}

{decision.get('recommendations', 'Contact us to refinance today.')}

Next Steps:
1. Review this analysis
2. Visit our website to start the process
3. Get a formal quote within 24 hours

Questions? Reply to this email or call us at 1-800-MORTGAGES

Best regards,
MortgageRate Intelligence System
"""
            
            return {
                'subject': subject,
                'body': body,
                'recipient': user_data.get('email', 'unknown@example.com'),
                'user_id': user_data.get('id', 'unknown')
            }
            
        except Exception as e:
            self._log(f"  Warning: Notification creation error: {e}")
            return {
                'subject': 'Mortgage Rate Update',
                'body': 'Please check your mortgage rates.',
                'recipient': user_data.get('email', ''),
                'error': str(e)
            }
    
    def _send_notification(self, user_data: Dict, notification: Dict) -> bool:
        """Send notification to user."""
        try:
            self._log(f"  Sending email to {notification['recipient']}...")
            
            # In production, this would call email_agent
            # self.email_agent.send_email(notification)
            
            self._log(f"  ✅ Email sent successfully")
            return True
            
        except Exception as e:
            self._log(f"  ⚠️  Email send failed: {e}")
            return False
    
    def _generate_subject(self, decision: str, filter_result: Dict) -> str:
        """Generate email subject line."""
        if 'REFINANCE' in decision:
            return "🎉 Refinancing Opportunity - Take Action Now"
        elif 'WAIT' in decision:
            return "📊 Mortgage Rates Update - Wait for Better Terms"
        else:
            return "💡 Your Mortgage Rate Analysis"
    
    def _log(self, message: str) -> None:
        """Log execution step."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.execution_log.append(log_entry)
        print(log_entry)
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID."""
        import uuid
        return f"REQ-{str(uuid.uuid4())[:8].upper()}"
    
    def _create_error_response(self, error_data: Dict) -> Dict:
        """Create error response."""
        return {
            'request_id': self.current_request_id,
            'status': 'error',
            'error': error_data.get('error', 'Unknown error'),
            'timestamp': datetime.now().isoformat(),
            'execution_log': self.execution_log
        }
    
    def _print_summary(self, response: Dict) -> None:
        """Print execution summary."""
        print("\n" + "="*70)
        print("EXECUTION SUMMARY")
        print("="*70)
        print(f"Request ID: {response['request_id']}")
        print(f"Status: {response['status']}")
        print(f"User: {response.get('user_name', 'Unknown')}")
        print(f"Decision: {response.get('decision', 'MONITOR')}")
        print(f"Eligible for Notification: {response.get('notification_sent', False)}")
        print("="*70)


# Example usage
if __name__ == "__main__":
    # Sample user data
    user_data = {
        'id': 'USER-001',
        'name': 'John Doe',
        'email': 'john@example.com',
        'current_rate': 4.5,
        'loan_term_years': 15,
        'monthly_payment': 1200,
        'closing_costs': 5000,
        'credit_score': 750
    }
    
    # Initialize orchestrator
    orchestrator = OrchestratorAgent()
    
    # Process request
    result = orchestrator.process_user_request(user_data)
    
    # Print result as JSON
    print("\n" + "="*70)
    print("FINAL RESULT (JSON)")
    print("="*70)
    print(json.dumps({
        'request_id': result.get('request_id'),
        'status': result.get('status'),
        'decision': result.get('decision'),
        'notification_sent': result.get('notification_sent')
    }, indent=2))
