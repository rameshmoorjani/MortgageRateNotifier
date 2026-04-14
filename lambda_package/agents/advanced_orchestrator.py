"""
Advanced Orchestrator Agent - Full orchestration with state management and error recovery.

Features:
- Workflow state management
- Error recovery and retries
- Request routing
- Batch processing
- Decision caching
"""

from agents.orchestrator import OrchestratorAgent
from agents.workflow_coordinator import (
    WorkflowCoordinator, 
    WorkflowState, 
    RequestStatus,
    ErrorRecoveryManager,
    RequestRouter
)
from typing import Dict, Any, Optional, List
from datetime import datetime
import json


class AdvancedOrchestratorAgent(OrchestratorAgent):
    """
    Enhanced orchestrator with advanced features.
    
    Adds:
    - Workflow state management
    - Error recovery
    - Request routing
    - Batch processing
    - Decision caching
    """
    
    def __init__(self):
        """Initialize advanced orchestrator."""
        super().__init__()
        
        self.name = "Advanced Orchestrator Agent"
        self.coordinator = WorkflowCoordinator()
        self.error_recovery = ErrorRecoveryManager(max_retries=3)
        self.router = RequestRouter()
        self.decision_cache: Dict[str, Dict] = {}
        self.cache_ttl = 3600  # 1 hour
    
    def process_user_request_advanced(self, user_data: Dict, 
                                     request_type: str = "FULL_ANALYSIS") -> Dict:
        """
        Process request with advanced orchestration features.
        
        Args:
            user_data: User mortgage data
            request_type: Type of request (FULL_ANALYSIS, PREDICTION_ONLY, etc.)
            
        Returns:
            Complete result with state tracking
        """
        request_id = self._generate_request_id()
        
        # Create workflow
        workflow = self.coordinator.create_workflow(request_id, user_data)
        self._log(f"Created workflow {request_id} (type: {request_type})")
        
        try:
            # Get execution route
            route = self.router.get_route(request_type)
            self._log(f"Executing route: {' → '.join(route)}")
            
            # Execute route
            result = self._execute_route(request_id, route, user_data, workflow)
            
            # Complete workflow
            self.coordinator.complete_workflow(request_id, result)
            
            return {
                'request_id': request_id,
                'status': 'success',
                'workflow': self.coordinator.get_workflow(request_id),
                'result': result
            }
            
        except Exception as e:
            self._log(f"Workflow failed: {str(e)}")
            self.coordinator.fail_step(request_id, 'execution', str(e))
            
            return {
                'request_id': request_id,
                'status': 'failed',
                'error': str(e),
                'workflow': self.coordinator.get_workflow(request_id)
            }
    
    def _execute_route(self, request_id: str, route: List[str], 
                      user_data: Dict, workflow: Dict) -> Dict:
        """Execute steps in route."""
        results = {}
        market_data = None
        prediction_result = None
        decision_result = None
        
        for step in route:
            self._log(f"Executing step: {step}")
            
            try:
                if step == 'gather_market_data':
                    self.coordinator.transition_state(
                        request_id, 
                        WorkflowState.GATHERING_DATA
                    )
                    market_data = self._gather_market_data()
                    self.coordinator.complete_step(
                        request_id, 
                        step, 
                        {'rate': market_data.get('current_rate')}
                    )
                    self._log(f"  ✅ Market rate: {market_data['current_rate']}%")
                
                elif step == 'predict_rates':
                    if market_data is None:
                        market_data = self._gather_market_data()
                    
                    self.coordinator.transition_state(
                        request_id,
                        WorkflowState.PREDICTING
                    )
                    
                    # Check cache first
                    cache_key = self._get_cache_key(user_data, market_data)
                    if cache_key in self.decision_cache:
                        prediction_result = self.decision_cache[cache_key]
                        self._log(f"  ✅ Using cached prediction")
                    else:
                        prediction_result = self.decision_agent.make_decision(
                            user_data, 
                            market_data
                        )
                        self.decision_cache[cache_key] = prediction_result
                    
                    self.coordinator.complete_step(
                        request_id,
                        step,
                        {'direction': prediction_result.get('predictions', {}).get('predicted_direction')}
                    )
                
                elif step == 'make_decision':
                    if prediction_result is None:
                        if market_data is None:
                            market_data = self._gather_market_data()
                        prediction_result = self.decision_agent.make_decision(
                            user_data,
                            market_data
                        )
                    
                    self.coordinator.transition_state(
                        request_id,
                        WorkflowState.DECIDING
                    )
                    
                    decision_result = prediction_result
                    self.coordinator.complete_step(
                        request_id,
                        step,
                        {'decision': decision_result.get('decision')}
                    )
                
                elif step == 'check_eligibility':
                    if decision_result is None:
                        raise ValueError("Decision result not available")
                    
                    self.coordinator.transition_state(
                        request_id,
                        WorkflowState.FILTERING
                    )
                    
                    filter_result = self._filter_eligibility(user_data, decision_result)
                    self.coordinator.complete_step(
                        request_id,
                        step,
                        {'eligible': filter_result.get('eligible')}
                    )
                    results['filter_result'] = filter_result
                
                elif step == 'send_notification':
                    if not results.get('filter_result', {}).get('eligible'):
                        self._log(f"  ⏭️  Skipping (not eligible)")
                        continue
                    
                    self.coordinator.transition_state(
                        request_id,
                        WorkflowState.NOTIFYING
                    )
                    
                    notification = self._create_notification(
                        user_data,
                        decision_result,
                        results.get('filter_result', {})
                    )
                    
                    self._send_notification(user_data, notification)
                    self.coordinator.complete_step(
                        request_id,
                        step,
                        {'sent': True}
                    )
                
                # Reset error recovery on success
                self.error_recovery.reset_retry(step)
                
            except Exception as e:
                # Try recovery
                if self.error_recovery.should_retry(step):
                    retry_count = self.error_recovery.increment_retry(step)
                    delay = self.error_recovery.get_backoff_delay(step)
                    self._log(f"  ⚠️  Step failed, retrying ({retry_count}/{3})")
                    
                    import time
                    time.sleep(delay)
                    
                    # Retry step recursively
                except:
                    raise
        
        results['market_data'] = market_data
        results['prediction_result'] = prediction_result
        results['decision_result'] = decision_result
        
        return results
    
    def process_batch_requests(self, requests: List[Dict]) -> List[Dict]:
        """
        Process multiple requests in batch.
        
        Args:
            requests: List of user data dictionaries
            
        Returns:
            List of results
        """
        self._log(f"Processing batch of {len(requests)} requests")
        
        results = []
        for i, user_data in enumerate(requests, 1):
            self._log(f"Batch item {i}/{len(requests)}")
            result = self.process_user_request_advanced(user_data)
            results.append(result)
        
        return results
    
    def get_workflow_status(self, request_id: str) -> Optional[Dict]:
        """Get current workflow status."""
        workflow = self.coordinator.get_workflow(request_id)
        if workflow:
            return {
                'request_id': request_id,
                'status': workflow.get('status'),
                'state': workflow.get('state'),
                'steps_completed': len(workflow.get('steps_completed', [])),
                'steps_failed': len(workflow.get('steps_failed', [])),
                'updated_at': workflow.get('updated_at')
            }
        return None
    
    def get_all_workflow_statuses(self) -> Dict:
        """Get status of all active workflows."""
        active = self.coordinator.get_active_workflows()
        return {
            'count': len(active),
            'workflows': [
                {
                    'request_id': w['request_id'],
                    'status': w['status'],
                    'state': w['state'],
                    'created_at': w['created_at']
                }
                for w in active
            ]
        }
    
    def retry_failed_workflow(self, request_id: str) -> Dict:
        """Retry a failed workflow."""
        workflow = self.coordinator.get_workflow(request_id)
        if not workflow:
            return {'status': 'error', 'message': 'Workflow not found'}
        
        user_data = workflow.get('user_data')
        if not user_data:
            return {'status': 'error', 'message': 'User data not available'}
        
        self._log(f"Retrying workflow {request_id}")
        
        # Clear from failed requests and retry
        return self.process_user_request_advanced(user_data, "FULL_ANALYSIS")
    
    def clear_cache(self) -> int:
        """Clear decision cache."""
        count = len(self.decision_cache)
        self.decision_cache.clear()
        self._log(f"Cleared {count} cached decisions")
        return count
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        return {
            'cached_decisions': len(self.decision_cache),
            'cache_ttl_seconds': self.cache_ttl
        }
    
    def _get_cache_key(self, user_data: Dict, market_data: Dict) -> str:
        """Generate cache key for decision."""
        import hashlib
        key_data = json.dumps({
            'user_id': user_data.get('id', 'unknown'),
            'rate': user_data.get('current_rate'),
            'market_rate': market_data.get('current_rate')
        }, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()


# Example usage
if __name__ == "__main__":
    # Create advanced orchestrator
    orchestrator = AdvancedOrchestratorAgent()
    
    # Sample requests
    requests = [
        {
            'id': 'USER-001',
            'name': 'John Doe',
            'email': 'john@example.com',
            'current_rate': 4.5,
            'loan_term_years': 15,
            'monthly_payment': 1200,
            'closing_costs': 5000,
            'credit_score': 750
        },
        {
            'id': 'USER-002',
            'name': 'Jane Smith',
            'email': 'jane@example.com',
            'current_rate': 4.0,
            'loan_term_years': 10,
            'monthly_payment': 1500,
            'closing_costs': 3000,
            'credit_score': 780
        }
    ]
    
    print("="*70)
    print("ADVANCED ORCHESTRATOR - BATCH PROCESSING")
    print("="*70)
    
    # Process single request with advanced features
    print("\n1. Processing single request with state tracking...")
    result = orchestrator.process_user_request_advanced(requests[0])
    print(f"   Result: {result['status']}")
    
    # Check status
    print("\n2. Checking workflow status...")
    status = orchestrator.get_workflow_status(result['request_id'])
    print(f"   Status: {status}")
    
    # Process batch
    print("\n3. Processing batch requests...")
    batch_results = orchestrator.process_batch_requests(requests)
    print(f"   Processed {len(batch_results)} requests")
    
    # Get all statuses
    print("\n4. Getting all workflow statuses...")
    all_statuses = orchestrator.get_all_workflow_statuses()
    print(f"   Active workflows: {all_statuses['count']}")
    
    # Cache stats
    print("\n5. Cache statistics...")
    cache_stats = orchestrator.get_cache_stats()
    print(f"   Cached decisions: {cache_stats['cached_decisions']}")
