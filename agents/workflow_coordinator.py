"""
Workflow Coordination Manager - Handles agent workflow logic.

Manages:
- Request routing
- Error recovery
- State persistence
- Workflow progress tracking
"""

from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from datetime import datetime
import json
from pathlib import Path


class WorkflowState(Enum):
    """Workflow execution states."""
    INITIALIZED = "initialized"
    GATHERING_DATA = "gathering_data"
    PREDICTING = "predicting"
    DECIDING = "deciding"
    FILTERING = "filtering"
    NOTIFYING = "notifying"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class RequestStatus(Enum):
    """Request statuses."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_FOR_ACTION = "waiting_for_action"


class WorkflowCoordinator:
    """
    Manages workflow execution, state transitions, and error recovery.
    """
    
    def __init__(self, state_dir: str = "workflow_state"):
        """Initialize coordinator."""
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(exist_ok=True)
        
        self.active_requests: Dict[str, Dict] = {}
        self.completed_requests: List[Dict] = []
        self.failed_requests: List[Dict] = []
    
    def create_workflow(self, request_id: str, user_data: Dict) -> Dict:
        """Create new workflow for request."""
        workflow = {
            'request_id': request_id,
            'user_data': user_data,
            'status': RequestStatus.PENDING.value,
            'state': WorkflowState.INITIALIZED.value,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'steps_completed': [],
            'steps_failed': [],
            'metadata': {},
            'error': None
        }
        
        self.active_requests[request_id] = workflow
        self._save_state(request_id, workflow)
        
        return workflow
    
    def transition_state(self, request_id: str, new_state: WorkflowState, 
                        metadata: Optional[Dict] = None) -> Dict:
        """Transition workflow to new state."""
        if request_id not in self.active_requests:
            raise ValueError(f"Request {request_id} not found")
        
        workflow = self.active_requests[request_id]
        old_state = workflow.get('state')
        
        # Validate state transition
        if not self._is_valid_transition(old_state, new_state.value):
            raise ValueError(f"Invalid transition: {old_state} → {new_state.value}")
        
        # Update workflow
        workflow['state'] = new_state.value
        workflow['updated_at'] = datetime.now().isoformat()
        workflow['status'] = RequestStatus.IN_PROGRESS.value
        
        if metadata:
            workflow['metadata'].update(metadata)
        
        self._save_state(request_id, workflow)
        
        return workflow
    
    def complete_step(self, request_id: str, step_name: str, 
                     result: Optional[Dict] = None) -> Dict:
        """Mark step as completed."""
        workflow = self.active_requests[request_id]
        
        step_record = {
            'step': step_name,
            'completed_at': datetime.now().isoformat(),
            'result': result
        }
        
        workflow['steps_completed'].append(step_record)
        workflow['updated_at'] = datetime.now().isoformat()
        
        self._save_state(request_id, workflow)
        
        return workflow
    
    def fail_step(self, request_id: str, step_name: str, error: str) -> Dict:
        """Mark step as failed."""
        workflow = self.active_requests[request_id]
        
        step_record = {
            'step': step_name,
            'failed_at': datetime.now().isoformat(),
            'error': error
        }
        
        workflow['steps_failed'].append(step_record)
        workflow['state'] = WorkflowState.FAILED.value
        workflow['status'] = RequestStatus.FAILED.value
        workflow['error'] = error
        workflow['updated_at'] = datetime.now().isoformat()
        
        self.failed_requests.append(workflow)
        del self.active_requests[request_id]
        
        self._save_state(request_id, workflow)
        
        return workflow
    
    def complete_workflow(self, request_id: str, result: Dict) -> Dict:
        """Mark workflow as completed."""
        workflow = self.active_requests[request_id]
        
        workflow['state'] = WorkflowState.COMPLETED.value
        workflow['status'] = RequestStatus.COMPLETED.value
        workflow['result'] = result
        workflow['completed_at'] = datetime.now().isoformat()
        workflow['updated_at'] = datetime.now().isoformat()
        
        self.completed_requests.append(workflow)
        del self.active_requests[request_id]
        
        self._save_state(request_id, workflow)
        
        return workflow
    
    def get_workflow(self, request_id: str) -> Optional[Dict]:
        """Get workflow by request ID."""
        if request_id in self.active_requests:
            return self.active_requests[request_id]
        
        # Try to load from disk
        return self._load_state(request_id)
    
    def get_active_workflows(self) -> List[Dict]:
        """Get all active workflows."""
        return list(self.active_requests.values())
    
    def get_workflow_stats(self) -> Dict:
        """Get workflow statistics."""
        return {
            'active': len(self.active_requests),
            'completed': len(self.completed_requests),
            'failed': len(self.failed_requests),
            'total': len(self.active_requests) + len(self.completed_requests) + len(self.failed_requests)
        }
    
    def _is_valid_transition(self, current_state: str, new_state: str) -> bool:
        """Validate state transitions."""
        valid_transitions = {
            WorkflowState.INITIALIZED.value: [
                WorkflowState.GATHERING_DATA.value,
                WorkflowState.FAILED.value
            ],
            WorkflowState.GATHERING_DATA.value: [
                WorkflowState.PREDICTING.value,
                WorkflowState.FAILED.value
            ],
            WorkflowState.PREDICTING.value: [
                WorkflowState.DECIDING.value,
                WorkflowState.FAILED.value
            ],
            WorkflowState.DECIDING.value: [
                WorkflowState.FILTERING.value,
                WorkflowState.FAILED.value
            ],
            WorkflowState.FILTERING.value: [
                WorkflowState.NOTIFYING.value,
                WorkflowState.COMPLETED.value,
                WorkflowState.FAILED.value
            ],
            WorkflowState.NOTIFYING.value: [
                WorkflowState.COMPLETED.value,
                WorkflowState.FAILED.value
            ],
            WorkflowState.PAUSED.value: [
                WorkflowState.GATHERING_DATA.value,
                WorkflowState.PREDICTING.value,
                WorkflowState.DECIDING.value,
                WorkflowState.FAILED.value
            ]
        }
        
        return new_state in valid_transitions.get(current_state, [])
    
    def _save_state(self, request_id: str, workflow: Dict) -> None:
        """Save workflow state to disk."""
        state_file = self.state_dir / f"{request_id}.json"
        with open(state_file, 'w') as f:
            json.dump(workflow, f, indent=2)
    
    def _load_state(self, request_id: str) -> Optional[Dict]:
        """Load workflow state from disk."""
        state_file = self.state_dir / f"{request_id}.json"
        if state_file.exists():
            with open(state_file, 'r') as f:
                return json.load(f)
        return None


class ErrorRecoveryManager:
    """
    Handles error recovery and retry logic.
    """
    
    def __init__(self, max_retries: int = 3):
        """Initialize recovery manager."""
        self.max_retries = max_retries
        self.retry_count: Dict[str, int] = {}
    
    def should_retry(self, step_name: str) -> bool:
        """Check if step should be retried."""
        retries = self.retry_count.get(step_name, 0)
        return retries < self.max_retries
    
    def increment_retry(self, step_name: str) -> int:
        """Increment retry count."""
        current = self.retry_count.get(step_name, 0)
        self.retry_count[step_name] = current + 1
        return self.retry_count[step_name]
    
    def reset_retry(self, step_name: str) -> None:
        """Reset retry count."""
        self.retry_count[step_name] = 0
    
    def get_retry_count(self, step_name: str) -> int:
        """Get current retry count."""
        return self.retry_count.get(step_name, 0)
    
    def get_backoff_delay(self, step_name: str) -> float:
        """Get exponential backoff delay in seconds."""
        retries = self.get_retry_count(step_name)
        return 2 ** retries  # 1s, 2s, 4s, 8s...


class RequestRouter:
    """
    Routes requests to appropriate agents.
    """
    
    def __init__(self):
        """Initialize router."""
        self.routes: Dict[str, List[str]] = {
            'FULL_ANALYSIS': [
                'gather_market_data',
                'predict_rates',
                'make_decision',
                'check_eligibility',
                'send_notification'
            ],
            'PREDICTION_ONLY': [
                'gather_market_data',
                'predict_rates'
            ],
            'DECISION_ONLY': [
                'predict_rates',
                'make_decision'
            ],
            'ELIGIBILITY_CHECK': [
                'check_eligibility'
            ]
        }
    
    def get_route(self, request_type: str) -> List[str]:
        """Get execution route for request type."""
        return self.routes.get(request_type, self.routes['FULL_ANALYSIS'])
    
    def register_route(self, name: str, steps: List[str]) -> None:
        """Register custom route."""
        self.routes[name] = steps


# Example usage
if __name__ == "__main__":
    # Create coordinator
    coordinator = WorkflowCoordinator()
    
    # Create workflow
    user_data = {'name': 'John Doe', 'email': 'john@example.com'}
    workflow = coordinator.create_workflow('REQ-001', user_data)
    print(f"Created workflow: {workflow['request_id']}")
    
    # Transition states
    coordinator.transition_state('REQ-001', WorkflowState.GATHERING_DATA)
    coordinator.complete_step('REQ-001', 'gather_market_data', {'rate': 4.2})
    
    coordinator.transition_state('REQ-001', WorkflowState.PREDICTING)
    coordinator.complete_step('REQ-001', 'predict_rates', {'prediction': 'DOWN'})
    
    # Complete workflow
    coordinator.complete_workflow('REQ-001', {'decision': 'REFINANCE'})
    
    # Print stats
    print(f"Workflow stats: {coordinator.get_workflow_stats()}")
    
    # Test router
    router = RequestRouter()
    route = router.get_route('FULL_ANALYSIS')
    print(f"Route steps: {route}")
