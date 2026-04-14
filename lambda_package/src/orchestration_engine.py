"""
Main Orchestration Entry Point - Simple interface for system orchestration.

This module provides a clean, unified interface for initiating orchestrated
workflows from the main application.
"""

from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from datetime import datetime
import json
import sys
from pathlib import Path

# Add agents to path for direct imports
sys.path.insert(0, str(Path(__file__).parent))

# Import directly to avoid circular dependencies from __init__.py
import importlib.util

# Load advanced_orchestrator directly
spec = importlib.util.spec_from_file_location(
    "advanced_orchestrator",
    Path(__file__).parent / "agents" / "advanced_orchestrator.py"
)
advanced_orchestrator_module = importlib.util.module_from_spec(spec)

try:
    spec.loader.exec_module(advanced_orchestrator_module)
    AdvancedOrchestratorAgent = advanced_orchestrator_module.AdvancedOrchestratorAgent
except Exception as e:
    print(f"Warning: Could not load advanced orchestrator: {e}")
    AdvancedOrchestratorAgent = None

# Load RAG modules for trustworthy decisions
TrustworthyDecisionAgent = None
try:
    # Load knowledge_base
    spec_kb = importlib.util.spec_from_file_location(
        "knowledge_base",
        Path(__file__).parent / "agents" / "knowledge_base.py"
    )
    kb_module = importlib.util.module_from_spec(spec_kb)
    spec_kb.loader.exec_module(kb_module)
    
    # Load rag_agent
    spec_rag = importlib.util.spec_from_file_location(
        "rag_agent",
        Path(__file__).parent / "agents" / "rag_agent.py"
    )
    rag_module = importlib.util.module_from_spec(spec_rag)
    rag_module.KnowledgeBase = kb_module.KnowledgeBase
    rag_module.Document = kb_module.Document
    spec_rag.loader.exec_module(rag_module)
    
    # Load trustworthy_decision_agent
    spec_tda = importlib.util.spec_from_file_location(
        "trustworthy_decision_agent",
        Path(__file__).parent / "agents" / "trustworthy_decision_agent.py"
    )
    tda_module = importlib.util.module_from_spec(spec_tda)
    tda_module.RAGAgent = rag_module.RAGAgent
    tda_module.ExplanationWithCitations = rag_module.ExplanationWithCitations
    spec_tda.loader.exec_module(tda_module)
    TrustworthyDecisionAgent = tda_module.TrustworthyDecisionAgent
except Exception as e:
    print(f"Warning: Could not load RAG system: {e}")


class NotificationStrategy(Enum):
    """Notification strategies."""
    ALWAYS = "always"          # Always notify if eligible
    NEVER = "never"            # Never notify
    HIGH_CONFIDENCE = "high"   # Only if confidence > 80%
    SIGNIFICANT_CHANGE = "sig" # Only if rate change > 0.25%


class MortgageOrchestrationEngine:
    """
    Main orchestration engine - Simple interface for orchestrated processing.
    
    Usage:
        engine = MortgageOrchestrationEngine()
        result = engine.process_user(user_data)
    """
    
    def __init__(self, notification_strategy: NotificationStrategy = NotificationStrategy.ALWAYS, use_rag: bool = True):
        """
        Initialize orchestration engine.
        
        Args:
            notification_strategy: Strategy for sending notifications
            use_rag: Enable RAG system for trustworthy decisions (default: True)
        """
        self.orchestrator = AdvancedOrchestratorAgent()
        self.notification_strategy = notification_strategy
        self.use_rag = use_rag and TrustworthyDecisionAgent is not None
        self.trustworthy_agent = TrustworthyDecisionAgent() if self.use_rag else None
        self.callbacks: Dict[str, List[Callable]] = {
            'on_start': [],
            'on_prediction': [],
            'on_decision': [],
            'on_trustworthy_decision': [],
            'on_complete': [],
            'on_error': []
        }
    
    def register_callback(self, event: str, callback: Callable) -> None:
        """
        Register a callback for an event.
        
        Args:
            event: Event name (on_start, on_prediction, on_decision, on_complete, on_error)
            callback: Function to call with (request_id, data)
        """
        if event in self.callbacks:
            self.callbacks[event].append(callback)
    
    def process_user(self, user_data: Dict) -> Dict:
        """
        Process a single user with full orchestration and optional RAG.
        
        Args:
            user_data: User mortgage and financial data
            
        Returns:
            Complete result with decision, RAG explanations, and notification status
        """
        request_id = self.orchestrator._generate_request_id()
        
        # Callback: on_start
        self._execute_callbacks('on_start', request_id, {'user_id': user_data.get('id')})
        
        try:
            # Process with orchestrator
            result = self.orchestrator.process_user_request_advanced(
                user_data,
                request_type='FULL_ANALYSIS'
            )
            
            # Callback: on_prediction
            if result['status'] == 'success':
                pred_data = result['result'].get('prediction_result', {})
                self._execute_callbacks('on_prediction', request_id, {
                    'direction': pred_data.get('predictions', {}).get('predicted_direction'),
                    'confidence': pred_data.get('reliability', {}).get('overall_reliability')
                })
                
                # Callback: on_decision
                dec_data = result['result'].get('decision_result', {})
                self._execute_callbacks('on_decision', request_id, {
                    'decision': dec_data.get('decision'),
                    'recommendation': dec_data.get('recommendation')
                })
                
                # RAG Integration: Generate trustworthy decision with citations
                if self.use_rag and self.trustworthy_agent:
                    try:
                        # Prepare prediction data for RAG
                        prediction = pred_data  # This includes predictions and reliability
                        
                        # Generate trustworthy decision
                        trustworthy_decision = self.trustworthy_agent.make_trustworthy_decision(
                            prediction, user_data
                        )
                        
                        # Add trustworthy decision to result
                        result['result']['trustworthy_decision'] = {
                            'decision': trustworthy_decision.decision,
                            'recommendation': trustworthy_decision.recommendation,
                            'confidence_score': trustworthy_decision.confidence_score,
                            'confidence_level': trustworthy_decision.confidence_level,
                            'explanation': trustworthy_decision.explanation.explanation,
                            'citations': [
                                {
                                    'title': c.title,
                                    'source': c.source,
                                    'relevance_score': c.relevance_score,
                                    'quote': c.quote
                                }
                                for c in trustworthy_decision.explanation.citations
                            ],
                            'financial_analysis': trustworthy_decision.financial_analysis,
                            'prediction_analysis': trustworthy_decision.prediction_analysis,
                            'risk_assessment': trustworthy_decision.risk_assessment,
                            'full_report': self.trustworthy_agent.get_full_report(trustworthy_decision)
                        }
                        
                        result['result']['rag_enabled'] = True
                        
                        # Callback: on_trustworthy_decision
                        self._execute_callbacks('on_trustworthy_decision', request_id, {
                            'trustworthy_decision': trustworthy_decision.decision,
                            'confidence_score': trustworthy_decision.confidence_score,
                            'citations_count': len(trustworthy_decision.explanation.citations)
                        })
                    except Exception as rag_error:
                        # Log RAG error but continue with basic decision
                        result['result']['rag_error'] = str(rag_error)
                        result['result']['rag_enabled'] = False
                        print(f"RAG processing error (continuing with basic decision): {rag_error}")
            
            # Callback: on_complete
            self._execute_callbacks('on_complete', request_id, {
                'status': result['status'],
                'notification_sent': result.get('notification_sent', False),
                'rag_enabled': result['result'].get('rag_enabled', False) if result['status'] == 'success' else False
            })
            
            return result
            
        except Exception as e:
            # Callback: on_error
            self._execute_callbacks('on_error', request_id, {'error': str(e)})
            
            return {
                'request_id': request_id,
                'status': 'error',
                'error': str(e)
            }
    
    def process_batch(self, user_list: List[Dict], verbose: bool = True) -> Dict:
        """
        Process batch of users.
        
        Args:
            user_list: List of user data dictionaries
            verbose: Print progress
            
        Returns:
            Batch results with summary statistics
        """
        results = []
        successful = 0
        notified = 0
        
        for i, user_data in enumerate(user_list, 1):
            if verbose:
                print(f"[{i}/{len(user_list)}] Processing {user_data.get('name', 'User')}...")
            
            result = self.process_user(user_data)
            results.append(result)
            
            if result['status'] == 'success':
                successful += 1
                if result.get('notification_sent'):
                    notified += 1
        
        summary = {
            'total': len(user_list),
            'successful': successful,
            'failed': len(user_list) - successful,
            'notified': notified,
            'notification_rate': notified / len(user_list) if user_list else 0,
            'results': results
        }
        
        if verbose:
            self._print_batch_summary(summary)
        
        return summary
    
    def schedule_daily_check(self, users: List[Dict], hour: int = 9) -> Dict:
        """
        Schedule daily check for users.
        
        Args:
            users: List of users to check
            hour: Hour to run check (0-23)
            
        Returns:
            Scheduled job info
        """
        # In production, this would use a scheduler like APScheduler
        # For now, return scheduling info
        return {
            'status': 'scheduled',
            'user_count': len(users),
            'scheduled_hour': hour,
            'next_run': self._get_next_run_time(hour),
            'note': 'Requires APScheduler integration'
        }
    
    def process_with_conditions(self, user_data: Dict, 
                               conditions: Optional[Dict] = None) -> Dict:
        """
        Process user with custom conditions.
        
        Args:
            user_data: User data
            conditions: Custom processing conditions
              - min_confidence: Minimum prediction confidence
              - min_savings: Minimum monthly savings required
              - max_fees: Maximum acceptable closing costs
              
        Returns:
            Result with condition evaluation
        """
        result = self.process_user(user_data)
        
        if conditions and result['status'] == 'success':
            evaluation = self._evaluate_conditions(result, conditions)
            result['conditions_met'] = evaluation['all_met']
            result['condition_details'] = evaluation['details']
        
        return result
    
    def analyze_prediction_accuracy(self) -> Dict:
        """
        Analyze prediction accuracy over time.
        
        Returns:
            Accuracy metrics and statistics
        """
        # Load completed workflows
        completed = self.orchestrator.coordinator.completed_requests
        
        if not completed:
            return {'status': 'no_data', 'message': 'No completed workflows'}
        
        # In production, compare predictions vs actual outcomes
        return {
            'total_predictions': len(completed),
            'message': 'Accuracy analysis requires actual outcome tracking'
        }
    
    def get_system_health(self) -> Dict:
        """
        Get system health metrics.
        
        Returns:
            Health status and metrics
        """
        stats = self.orchestrator.coordinator.get_workflow_stats()
        cache_stats = self.orchestrator.get_cache_stats()
        
        health = {
            'status': 'healthy' if stats['failed'] < 5 else 'degraded',
            'workflows': {
                'active': stats['active'],
                'completed': stats['completed'],
                'failed': stats['failed'],
                'total': stats['total']
            },
            'cache': cache_stats,
            'timestamp': datetime.now().isoformat()
        }
        
        return health
    
    def export_results(self, request_id: str, format: str = 'json') -> str:
        """
        Export workflow results.
        
        Args:
            request_id: Request ID
            format: Output format ('json', 'csv', 'xlsx')
            
        Returns:
            Formatted result data
        """
        workflow = self.orchestrator.coordinator.get_workflow(request_id)
        
        if not workflow:
            return json.dumps({'error': 'Workflow not found'})
        
        if format == 'json':
            return json.dumps(workflow, indent=2)
        else:
            return f"Format {format} not yet implemented"
    
    def _execute_callbacks(self, event: str, request_id: str, data: Dict) -> None:
        """Execute callbacks for event."""
        for callback in self.callbacks.get(event, []):
            try:
                callback(request_id, data)
            except Exception as e:
                print(f"Callback error for {event}: {e}")
    
    def _evaluate_conditions(self, result: Dict, conditions: Dict) -> Dict:
        """Evaluate custom conditions."""
        details = {}
        all_met = True
        
        decision = result['result'].get('decision_result', {})
        financial = decision.get('financial_analysis', {})
        
        # Check confidence
        if 'min_confidence' in conditions:
            confidence = decision.get('reliability', {}).get('overall_reliability', 0)
            met = confidence >= conditions['min_confidence']
            details['confidence'] = {
                'required': conditions['min_confidence'],
                'actual': confidence,
                'met': met
            }
            all_met = all_met and met
        
        # Check savings
        if 'min_savings' in conditions:
            savings = financial.get('potential_monthly_saving', 0)
            met = savings >= conditions['min_savings']
            details['savings'] = {
                'required': conditions['min_savings'],
                'actual': savings,
                'met': met
            }
            all_met = all_met and met
        
        # Check fees
        if 'max_fees' in conditions:
            fees = financial.get('estimated_closing_costs', 0)
            met = fees <= conditions['max_fees']
            details['fees'] = {
                'maximum': conditions['max_fees'],
                'actual': fees,
                'met': met
            }
            all_met = all_met and met
        
        return {'all_met': all_met, 'details': details}
    
    def _print_batch_summary(self, summary: Dict) -> None:
        """Print batch processing summary."""
        print("\n" + "="*60)
        print("BATCH PROCESSING SUMMARY")
        print("="*60)
        print(f"Total Processed:      {summary['total']}")
        print(f"Successful:           {summary['successful']}")
        print(f"Failed:               {summary['failed']}")
        print(f"Notified:             {summary['notified']}")
        print(f"Notification Rate:    {summary['notification_rate']*100:.1f}%")
        print("="*60)
    
    def _get_next_run_time(self, hour: int) -> str:
        """Calculate next run time."""
        from datetime import datetime, timedelta
        
        now = datetime.now()
        next_run = now.replace(hour=hour, minute=0, second=0)
        
        if next_run <= now:
            next_run += timedelta(days=1)
        
        return next_run.isoformat()


# Example usage
if __name__ == "__main__":
    # Create orchestration engine
    engine = MortgageOrchestrationEngine()
    
    # Register callbacks
    def on_prediction_callback(request_id, data):
        print(f"[CALLBACK] Prediction: {data['direction']} ({data['confidence']*100:.0f}%)")
    
    engine.register_callback('on_prediction', on_prediction_callback)
    
    # Sample user
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
    
    # Process user
    print("Processing user...")
    result = engine.process_user(user_data)
    
    # Check health
    print("\nSystem Health:")
    health = engine.get_system_health()
    print(f"Status: {health['status']}")
    print(f"Active workflows: {health['workflows']['active']}")
    print(f"Cached decisions: {health['cache']['cached_decisions']}")
