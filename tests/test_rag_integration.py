#!/usr/bin/env python3
"""
RAG Integration Test - Batch process sample users with trustworthy decisions.

Tests the integration of TrustworthyDecisionAgent into MortgageOrchestrationEngine.
"""

import json
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Set dummy API key to satisfy config requirements
import os
os.environ['OPENAI_API_KEY'] = 'sk-test-rag-integration'

from orchestration_engine import MortgageOrchestrationEngine, NotificationStrategy


def load_sample_users(filepath: str = 'users.json') -> list:
    """Load sample users from JSON file."""
    try:
        with open(filepath, 'r') as f:
            users = json.load(f)
        return users
    except FileNotFoundError:
        print(f"Sample users file not found: {filepath}")
        print("Creating sample users...")
        
        # Create sample users if file doesn't exist
        sample_users = [
            {
                'id': 'USER-001',
                'name': 'Sarah Johnson',
                'email': 'sarah@example.com',
                'current_rate': 4.5,
                'loan_term_years': 20,
                'monthly_payment': 1200,
                'closing_costs': 5500,
                'credit_score': 750,
                'loan_amount': 350000,
                'remaining_term': 240
            },
            {
                'id': 'USER-002',
                'name': 'Mike Chen',
                'email': 'mike@example.com',
                'current_rate': 5.2,
                'loan_term_years': 30,
                'monthly_payment': 1800,
                'closing_costs': 6000,
                'credit_score': 720,
                'loan_amount': 400000,
                'remaining_term': 300
            },
            {
                'id': 'USER-003',
                'name': 'Emily Rodriguez',
                'email': 'emily@example.com',
                'current_rate': 4.0,
                'loan_term_years': 15,
                'monthly_payment': 1500,
                'closing_costs': 4500,
                'credit_score': 780,
                'loan_amount': 250000,
                'remaining_term': 180
            },
            {
                'id': 'USER-004',
                'name': 'James Wilson',
                'email': 'james@example.com',
                'current_rate': 4.8,
                'loan_term_years': 25,
                'monthly_payment': 1400,
                'closing_costs': 5800,
                'credit_score': 710,
                'loan_amount': 320000,
                'remaining_term': 300
            },
            {
                'id': 'USER-005',
                'name': 'Lisa Anderson',
                'email': 'lisa@example.com',
                'current_rate': 4.2,
                'loan_term_years': 20,
                'monthly_payment': 1100,
                'closing_costs': 4800,
                'credit_score': 760,
                'loan_amount': 300000,
                'remaining_term': 240
            }
        ]
        
        with open(filepath, 'w') as f:
            json.dump(sample_users, f, indent=2)
        
        return sample_users


def print_user_result(result: dict, user_name: str = 'User') -> None:
    """Print formatted result for a user."""
    print(f"\n{'='*80}")
    print(f"USER: {user_name}")
    print(f"{'='*80}")
    
    if result['status'] != 'success':
        print(f"Status: ERROR - {result.get('error', 'Unknown error')}")
        return
    
    result_data = result.get('result', {})
    
    # Basic prediction
    pred = result_data.get('prediction_result', {})
    print(f"\n[PREDICTION]")
    print(f"  Direction: {pred.get('predictions', {}).get('predicted_direction')}")
    print(f"  Confidence: {pred.get('reliability', {}).get('overall_reliability')*100:.0f}%")
    print(f"  Avg Rate (30d): {pred.get('predictions', {}).get('predicted_average_30d')}%")
    
    # Basic decision
    dec = result_data.get('decision_result', {})
    print(f"\n[BASIC DECISION]")
    print(f"  Decision: {dec.get('decision')}")
    print(f"  Recommendation: {dec.get('recommendation')[:60]}...")
    
    # RAG trustworthy decision
    trustworthy = result_data.get('trustworthy_decision')
    if trustworthy:
        print(f"\n[RAG TRUSTWORTHY DECISION] ✓ RAG ENABLED")
        print(f"  Decision: {trustworthy['decision']}")
        print(f"  Confidence: {trustworthy['confidence_score']*100:.0f}% ({trustworthy['confidence_level'].upper()})")
        print(f"  Recommendation: {trustworthy['recommendation'][:60]}...")
        print(f"  Citations: {len(trustworthy['citations'])} sources")
        
        if trustworthy['citations']:
            print(f"\n  [TOP CITATION]")
            cite = trustworthy['citations'][0]
            print(f"    - {cite['title']} ({cite['source']})")
            print(f"    - Relevance: {cite['relevance_score']*100:.0f}%")
            print(f"    - Quote: \"{cite['quote'][:50]}...\"")
        
        print(f"\n  [RISK ASSESSMENT]")
        print(f"    {trustworthy['risk_assessment']}")
    else:
        rag_error = result_data.get('rag_error')
        if rag_error:
            print(f"\n[RAG TRUSTWORTHY DECISION] ✗ RAG DISABLED")
            print(f"  Error: {rag_error}")
        else:
            print(f"\n[RAG TRUSTWORTHY DECISION] ✗ RAG NOT ENABLED")


def test_rag_integration():
    """Test RAG integration with batch processing."""
    print("\n" + "="*80)
    print("RAG INTEGRATION TEST - BATCH PROCESSING")
    print("="*80)
    
    # Load sample users
    print("\n[STEP 1] Loading sample users...")
    users = load_sample_users()
    print(f"[OK] Loaded {len(users)} sample users")
    
    # Create orchestration engine with RAG
    print("\n[STEP 2] Initializing orchestration engine with RAG...")
    engine = MortgageOrchestrationEngine(
        notification_strategy=NotificationStrategy.ALWAYS,
        use_rag=True
    )
    
    if engine.use_rag:
        print("[OK] Orchestration engine initialized with RAG enabled")
    else:
        print("[WARNING] RAG not available - proceeding with basic decisions only")
    
    # Register callbacks
    print("\n[STEP 3] Registering callbacks...")
    
    def on_prediction(req_id, data):
        print(f"  [CALLBACK] Prediction: {data['direction']} ({data['confidence']*100:.0f}%)")
    
    def on_trustworthy_decision(req_id, data):
        print(f"  [CALLBACK] Trustworthy Decision: {data['trustworthy_decision']} ({data['confidence_score']*100:.0f}%)")
        print(f"  [CALLBACK] Citations: {data['citations_count']} sources")
    
    engine.register_callback('on_prediction', on_prediction)
    engine.register_callback('on_trustworthy_decision', on_trustworthy_decision)
    print("[OK] Callbacks registered")
    
    # Process batch
    print("\n[STEP 4] Processing batch of users...")
    print("=" * 80)
    
    summary = engine.process_batch(users, verbose=True)
    
    # Print detailed results for each user
    print("\n[STEP 5] Detailed results:")
    for i, (user, result) in enumerate(zip(users, summary['results']), 1):
        print_user_result(result, user.get('name', f'User {i}'))
    
    # Print batch summary
    print("\n" + "="*80)
    print("BATCH SUMMARY")
    print("="*80)
    print(f"Total Processed:    {summary['total']}")
    print(f"Successful:         {summary['successful']}")
    print(f"Failed:             {summary['failed']}")
    print(f"Notification Rate:  {summary['notification_rate']*100:.1f}%")
    
    # Calculate RAG success rate
    rag_results = [r for r in summary['results'] if r['status'] == 'success' and r['result'].get('rag_enabled')]
    rag_rate = len(rag_results) / summary['successful'] if summary['successful'] > 0 else 0
    print(f"RAG Success Rate:   {rag_rate*100:.1f}% ({len(rag_results)}/{summary['successful']})")
    print("="*80)
    
    # Validation
    print("\n[VALIDATION]")
    if summary['successful'] >= 4:
        print("✓ Successful: Processed 4+ users successfully")
    else:
        print(f"✗ Failed: Only processed {summary['successful']} users successfully (need 4+)")
    
    if rag_rate >= 0.8:
        print("✓ Successful: RAG enabled for 80%+ of users")
    else:
        print(f"✗ Failed: RAG only enabled for {rag_rate*100:.0f}% of users (need 80%+)")
    
    if all(r['result'].get('trustworthy_decision', {}).get('citations') for r in summary['results'] if r['status'] == 'success' and r['result'].get('rag_enabled')):
        print("✓ Successful: All RAG decisions include citations")
    else:
        print("✗ Failed: Some RAG decisions missing citations")
    
    print("\n" + "="*80)
    if summary['successful'] >= 4 and rag_rate >= 0.8:
        print("[SUCCESS] RAG Integration Test PASSED!")
    else:
        print("[INCOMPLETE] RAG Integration Test needs attention")
    print("="*80)
    
    return 0 if summary['successful'] >= 4 and rag_rate >= 0.8 else 1


if __name__ == "__main__":
    exit_code = test_rag_integration()
    sys.exit(exit_code)
