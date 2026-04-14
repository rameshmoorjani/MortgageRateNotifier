"""
Orchestration Test Suite - Examples and integration tests for the orchestration layer.

This file demonstrates:
1. Basic orchestration workflow
2. Advanced stateful orchestration
3. Batch processing
4. Error recovery
5. Integration with existing agents
"""

import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.orchestrator import OrchestratorAgent
from agents.advanced_orchestrator import AdvancedOrchestratorAgent
from agents.workflow_coordinator import WorkflowState
import json
from datetime import datetime


def test_basic_orchestration():
    """Test basic orchestration workflow."""
    print("\n" + "="*70)
    print("TEST 1: Basic Orchestration Workflow")
    print("="*70)
    
    orchestrator = OrchestratorAgent()
    
    user_data = {
        'id': 'TEST-001',
        'name': 'Test User',
        'email': 'test@example.com',
        'current_rate': 4.5,
        'loan_term_years': 15,
        'monthly_payment': 1200,
        'closing_costs': 5000,
        'credit_score': 750
    }
    
    result = orchestrator.process_user_request(user_data)
    
    print("\nResult Summary:")
    print(f"  Status: {result.get('status')}")
    print(f"  Decision: {result.get('decision')}")
    print(f"  Notification Sent: {result.get('notification_sent')}")
    
    return result


def test_advanced_orchestration():
    """Test advanced orchestration with state management."""
    print("\n" + "="*70)
    print("TEST 2: Advanced Orchestration with State Management")
    print("="*70)
    
    orchestrator = AdvancedOrchestratorAgent()
    
    user_data = {
        'id': 'TEST-002',
        'name': 'Advanced Test',
        'email': 'advanced@example.com',
        'current_rate': 4.0,
        'loan_term_years': 20,
        'monthly_payment': 1100,
        'closing_costs': 4000,
        'credit_score': 700
    }
    
    result = orchestrator.process_user_request_advanced(
        user_data,
        request_type="FULL_ANALYSIS"
    )
    
    print("\nResult Summary:")
    print(f"  Status: {result.get('status')}")
    print(f"  Request ID: {result.get('request_id')}")
    
    workflow = result.get('workflow', {})
    print(f"  Workflow State: {workflow.get('state')}")
    print(f"  Steps Completed: {len(workflow.get('steps_completed', []))}")
    
    return result


def test_batch_processing():
    """Test batch processing of multiple requests."""
    print("\n" + "="*70)
    print("TEST 3: Batch Processing")
    print("="*70)
    
    orchestrator = AdvancedOrchestratorAgent()
    
    # Create test batch
    batch = [
        {
            'id': f'BATCH-{i:03d}',
            'name': f'User {i}',
            'email': f'user{i}@example.com',
            'current_rate': 3.5 + (i * 0.1),
            'loan_term_years': 15 + (i % 10),
            'monthly_payment': 1000 + (i * 50),
            'closing_costs': 3000 + (i * 200),
            'credit_score': 700 + (i % 100)
        }
        for i in range(3)
    ]
    
    print(f"Processing {len(batch)} requests...")
    results = orchestrator.process_batch_requests(batch)
    
    print("\nBatch Results:")
    for r in results:
        print(f"  {r['request_id']}: {r['status']}")
    
    stats = orchestrator.coordinator.get_workflow_stats()
    print(f"\nOverall Stats:")
    print(f"  Completed: {stats['completed']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Active: {stats['active']}")
    
    return results


def test_prediction_only():
    """Test prediction-only workflow (no notification)."""
    print("\n" + "="*70)
    print("TEST 4: Prediction-Only Workflow")
    print("="*70)
    
    orchestrator = AdvancedOrchestratorAgent()
    
    user_data = {
        'id': 'TEST-004',
        'name': 'Prediction Test',
        'email': 'prediction@example.com',
        'current_rate': 4.5,
        'loan_term_years': 15,
        'monthly_payment': 1200,
        'closing_costs': 5000,
        'credit_score': 750
    }
    
    result = orchestrator.process_user_request_advanced(
        user_data,
        request_type="PREDICTION_ONLY"
    )
    
    print("\nResult Summary:")
    print(f"  Status: {result.get('status')}")
    print(f"  Request ID: {result.get('request_id')}")
    
    workflow = result.get('workflow', {})
    steps = [s['step'] for s in workflow.get('steps_completed', [])]
    print(f"  Steps Executed: {', '.join(steps)}")
    
    return result


def test_workflow_status_tracking():
    """Test workflow status tracking."""
    print("\n" + "="*70)
    print("TEST 5: Workflow Status Tracking")
    print("="*70)
    
    orchestrator = AdvancedOrchestratorAgent()
    
    user_data = {
        'id': 'TEST-005',
        'name': 'Status Test',
        'email': 'status@example.com',
        'current_rate': 4.2,
        'loan_term_years': 10,
        'monthly_payment': 1300,
        'closing_costs': 4500,
        'credit_score': 720
    }
    
    # Process request
    result = orchestrator.process_user_request_advanced(user_data)
    request_id = result['request_id']
    
    # Get status
    status = orchestrator.get_workflow_status(request_id)
    
    print("\nWorkflow Status:")
    print(f"  Request ID: {status['request_id']}")
    print(f"  Status: {status['status']}")
    print(f"  State: {status['state']}")
    print(f"  Steps Completed: {status['steps_completed']}")
    print(f"  Updated: {status['updated_at']}")
    
    # Get all statuses
    all_statuses = orchestrator.get_all_workflow_statuses()
    print(f"\nAll Workflows:")
    print(f"  Total: {all_statuses['count']}")
    
    return status


def test_cache_functionality():
    """Test decision caching."""
    print("\n" + "="*70)
    print("TEST 6: Decision Caching")
    print("="*70)
    
    orchestrator = AdvancedOrchestratorAgent()
    
    user_data = {
        'id': 'TEST-006',
        'name': 'Cache Test',
        'email': 'cache@example.com',
        'current_rate': 4.5,
        'loan_term_years': 15,
        'monthly_payment': 1200,
        'closing_costs': 5000,
        'credit_score': 750
    }
    
    print("First request (will be cached)...")
    result1 = orchestrator.process_user_request_advanced(
        user_data,
        request_type="PREDICTION_ONLY"
    )
    
    print("Second request (should use cache)...")
    result2 = orchestrator.process_user_request_advanced(
        user_data,
        request_type="PREDICTION_ONLY"
    )
    
    cache_stats = orchestrator.get_cache_stats()
    print(f"\nCache Statistics:")
    print(f"  Cached Decisions: {cache_stats['cached_decisions']}")
    print(f"  Cache TTL: {cache_stats['cache_ttl_seconds']}s")
    
    return cache_stats


def test_error_handling():
    """Test error handling and recovery."""
    print("\n" + "="*70)
    print("TEST 7: Error Handling & Recovery")
    print("="*70)
    
    orchestrator = AdvancedOrchestratorAgent()
    
    # Test with invalid data
    invalid_user_data = {
        'id': 'TEST-007',
        'name': 'Error Test',
        # Missing required fields
    }
    
    print("Processing request with invalid data...")
    try:
        result = orchestrator.process_user_request_advanced(invalid_user_data)
        print(f"\nResult:")
        print(f"  Status: {result.get('status')}")
        if result.get('status') == 'failed':
            print(f"  Error: {result.get('error')}")
    except Exception as e:
        print(f"  Exception caught: {str(e)}")


def run_all_tests():
    """Run all orchestration tests."""
    print("\n" + "#"*70)
    print("# ORCHESTRATION TEST SUITE")
    print("#"*70)
    print(f"Started: {datetime.now().isoformat()}")
    
    tests = [
        ("Basic Orchestration", test_basic_orchestration),
        ("Advanced Orchestration", test_advanced_orchestration),
        ("Batch Processing", test_batch_processing),
        ("Prediction-Only Workflow", test_prediction_only),
        ("Workflow Status Tracking", test_workflow_status_tracking),
        ("Decision Caching", test_cache_functionality),
        ("Error Handling", test_error_handling),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            test_func()
            results.append((test_name, "✅ PASS"))
        except Exception as e:
            print(f"\n❌ TEST FAILED: {str(e)}")
            results.append((test_name, f"❌ FAIL: {str(e)}"))
    
    # Summary
    print("\n" + "#"*70)
    print("# TEST SUMMARY")
    print("#"*70)
    for test_name, result in results:
        print(f"{test_name:40} {result}")
    
    passed = sum(1 for _, r in results if "PASS" in r)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    print(f"Ended: {datetime.now().isoformat()}")


if __name__ == "__main__":
    run_all_tests()
