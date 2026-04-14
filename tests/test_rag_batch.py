#!/usr/bin/env python3
"""
RAG Integration Test - Batch process sample users using working RAG modules.

This test demonstrates RAG integration by batch processing 5 users
and validating that each gets trustworthy decisions with citations.
"""

import os
import sys
import importlib.util
from pathlib import Path

# Set a dummy API key
os.environ['OPENAI_API_KEY'] = 'sk-test-rag-integration'

def load_rag_modules():
    """Load RAG modules directly, avoiding __init__.py cascade."""
    # Load knowledge_base module
    spec = importlib.util.spec_from_file_location(
        "knowledge_base",
        "agents/knowledge_base.py"
    )
    kb_module = importlib.util.module_from_spec(spec)
    sys.modules['agents.knowledge_base'] = kb_module
    spec.loader.exec_module(kb_module)
    
    # Load rag_agent module
    spec = importlib.util.spec_from_file_location(
        "rag_agent",
        "agents/rag_agent.py"
    )
    rag_module = importlib.util.module_from_spec(spec)
    rag_module.KnowledgeBase = kb_module.KnowledgeBase
    rag_module.Document = kb_module.Document
    sys.modules['agents.rag_agent'] = rag_module
    spec.loader.exec_module(rag_module)
    
    # Load trustworthy_decision_agent module
    spec = importlib.util.spec_from_file_location(
        "trustworthy_decision_agent",
        "agents/trustworthy_decision_agent.py"
    )
    tda_module = importlib.util.module_from_spec(spec)
    tda_module.RAGAgent = rag_module.RAGAgent
    tda_module.ExplanationWithCitations = rag_module.ExplanationWithCitations
    sys.modules['agents.trustworthy_decision_agent'] = tda_module
    spec.loader.exec_module(tda_module)
    
    return tda_module.TrustworthyDecisionAgent


def mock_orchestrator_output(user):
    """Simulate an orchestrator prediction output for a user."""
    return {
        'predictions': {
            'predicted_direction': 'DOWN',
            'predicted_average_30d': 4.0,
            'min_rate': 3.9,
            'max_rate': 4.1
        },
        'reliability': {'overall_reliability': 0.82},
        'financial_analysis': {
            'current_rate': user.get('current_rate', 4.5),
            'potential_monthly_saving': 250,
            'estimated_closing_costs': 5500,
            'breakeven_months': 22,
            'remaining_loan_term_months': user.get('remaining_term', 240),
            'is_financially_safe': True,
            'current_loan_amount': user.get('loan_amount', 350000)
        }
    }


def test_batch_integration():
    """Test RAG integration with batch processing."""
    print("\n" + "="*80)
    print("RAG BATCH INTEGRATION TEST")
    print("="*80)
    
    # Step 1: Load RAG system
    print("\n[STEP 1] Loading RAG system...")
    try:
        TrustworthyDecisionAgent = load_rag_modules()
        print("[OK] RAG system loaded")
    except Exception as e:
        print(f"[ERROR] Failed to load RAG: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Step 2: Sample users
    print("\n[STEP 2] Creating sample users...")
    users = [
        {'id': 'U001', 'name': 'Sarah Johnson', 'current_rate': 4.5, 'loan_amount': 350000, 'remaining_term': 240, 'credit_score': 750},
        {'id': 'U002', 'name': 'Mike Chen', 'current_rate': 5.2, 'loan_amount': 400000, 'remaining_term': 300, 'credit_score': 720},
        {'id': 'U003', 'name': 'Emily Rodriguez', 'current_rate': 4.0, 'loan_amount': 250000, 'remaining_term': 180, 'credit_score': 780},
        {'id': 'U004', 'name': 'James Wilson', 'current_rate': 4.8, 'loan_amount': 320000, 'remaining_term': 300, 'credit_score': 710},
        {'id': 'U005', 'name': 'Lisa Anderson', 'current_rate': 4.2, 'loan_amount': 300000, 'remaining_term': 240, 'credit_score': 760},
    ]
    print(f"[OK] Created {len(users)} sample users")
    
    # Step 3: Initialize agent
    print("\n[STEP 3] Initializing TrustworthyDecisionAgent...")
    try:
        agent = TrustworthyDecisionAgent()
        print("[OK] Agent initialized")
    except Exception as e:
        print(f"[ERROR] Failed to init agent: {e}")
        return 1
    
    # Step 4: Batch process
    print("\n[STEP 4] Processing batch...")
    print("="*80)
    
    results = []
    for i, user in enumerate(users, 1):
        print(f"\n[{i}/5] {user['name']}")
        try:
            # Get mock orchestrator output
            prediction = mock_orchestrator_output(user)
            
            # Generate trustworthy decision
            decision = agent.make_trustworthy_decision(prediction, user)
            
            # Store result
            result = {
                'user': user['name'],
                'status': 'success',
                'decision': decision.decision,
                'confidence': decision.confidence_score,
                'citations': len(decision.explanation.citations),
                'has_risk': bool(decision.risk_assessment)
            }
            results.append(result)
            
            print(f"     Decision: {decision.decision}")
            print(f"     Confidence: {decision.confidence_score*100:.0f}%")
            print(f"     Citations: {len(decision.explanation.citations)}")
            print(f"     Risk: {decision.risk_assessment.split(chr(10))[0][:50]}")
            
        except Exception as e:
            print(f"     [ERROR] {e}")
            results.append({'user': user['name'], 'status': 'error', 'error': str(e)})
    
    # Step 5: Summary
    print("\n" + "="*80)
    print("BATCH SUMMARY")
    print("="*80)
    
    successful = sum(1 for r in results if r['status'] == 'success')
    with_citations = sum(1 for r in results if r['status'] == 'success' and r['citations'] > 0)
    
    print(f"Total Processed:      {len(results)}")
    print(f"Successful:           {successful}")
    print(f"With Citations:       {with_citations}")
    print(f"Success Rate:         {successful/len(results)*100:.0f}%")
    print(f"Citation Rate:        {with_citations/successful*100:.0f}%" if successful > 0 else "0%")
    print("="*80)
    
    # Validation
    print("\n[VALIDATION RESULTS]")
    passed = True
    
    if successful >= 4:
        print("[PASS] Processed 4+ users successfully")
    else:
        print(f"[FAIL] Only processed {successful} users (need 4+)")
        passed = False
    
    if with_citations >= 4:
        print("[PASS] Generated citations for 4+ users")
    else:
        print(f"[FAIL] Only generated citations for {with_citations} users (need 4+)")
        passed = False
    
    if all(r.get('has_risk') for r in results if r['status'] == 'success'):
        print("[PASS] All decisions include risk assessment")
    else:
        print("[FAIL] Some decisions missing risk assessment")
        passed = False
    
    print("\n" + "="*80)
    if passed:
        print("[SUCCESS] RAG Integration Test PASSED!")
        print("="*80)
        return 0
    else:
        print("[FAILURE] RAG Integration Test Failed")
        print("="*80)
        return 1


if __name__ == "__main__":
    exit_code = test_batch_integration()
    sys.exit(exit_code)
