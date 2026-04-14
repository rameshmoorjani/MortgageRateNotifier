#!/usr/bin/env python3
"""
RAG Integration Test (Simplified) - Test RAG within mock orchestration.

This test validates that TrustworthyDecisionAgent integrates properly
with orchestration by simulating the orchestrator's output.
"""

import json
import sys
import os
from pathlib import Path

# Mock dotenv to avoid import errors
class MockDotenv:
    def load_dotenv(self):
        pass

sys.modules['dotenv'] = MockDotenv()
from dotenv import load_dotenv
load_dotenv = lambda: None

# Set all required environment variables FIRST
os.environ['OPENAI_API_KEY'] = 'sk-test-rag-integration'
os.environ['SEARCH_API_KEY'] = 'test-key'
os.environ['GOOGLE_API_KEY'] = 'test-key'
os.environ['SEARCH_ENGINE_ID'] = 'test-id'

sys.path.insert(0, str(Path(__file__).parent))

import importlib.util


def load_rag_system():
    """Load RAG modules directly."""
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
    
    return tda_module.TrustworthyDecisionAgent


def create_mock_orchestrator_result(user_data):
    """Create a mock orchestrator result with predictions and financial analysis."""
    return {
        'predictions': {
            'predicted_direction': 'DOWN',
            'predicted_average_30d': 4.0,
            'min_rate': 3.9,
            'max_rate': 4.1
        },
        'reliability': {
            'overall_reliability': 0.82
        },
        'financial_analysis': {
            'current_rate': user_data.get('current_rate', 4.5),
            'potential_monthly_saving': 250,
            'estimated_closing_costs': 5500,
            'breakeven_months': 22,
            'remaining_loan_term_months': user_data.get('remaining_term', 240),
            'is_financially_safe': True,
            'current_loan_amount': user_data.get('loan_amount', 350000)
        }
    }


def test_rag_integration():
    """Test RAG integration with sample users."""
    print("\n" + "="*80)
    print("RAG INTEGRATION TEST - SIMPLIFIED")
    print("="*80)
    
    # Load RAG system
    print("\n[STEP 1] Loading RAG system...")
    try:
        TrustworthyDecisionAgent = load_rag_system()
        print("[OK] RAG system loaded successfully")
    except Exception as e:
        print(f"[ERROR] Failed to load RAG system: {e}")
        return 1
    
    # Load sample users
    print("\n[STEP 2] Loading sample users...")
    sample_users = [
        {
            'id': 'USER-001',
            'name': 'Sarah Johnson',
            'current_rate': 4.5,
            'loan_amount': 350000,
            'remaining_term': 240,
            'credit_score': 750
        },
        {
            'id': 'USER-002',
            'name': 'Mike Chen',
            'current_rate': 5.2,
            'loan_amount': 400000,
            'remaining_term': 300,
            'credit_score': 720
        },
        {
            'id': 'USER-003',
            'name': 'Emily Rodriguez',
            'current_rate': 4.0,
            'loan_amount': 250000,
            'remaining_term': 180,
            'credit_score': 780
        },
        {
            'id': 'USER-004',
            'name': 'James Wilson',
            'current_rate': 4.8,
            'loan_amount': 320000,
            'remaining_term': 300,
            'credit_score': 710
        },
        {
            'id': 'USER-005',
            'name': 'Lisa Anderson',
            'current_rate': 4.2,
            'loan_amount': 300000,
            'remaining_term': 240,
            'credit_score': 760
        }
    ]
    print(f"[OK] Loaded {len(sample_users)} sample users")
    
    # Initialize RAG agent
    print("\n[STEP 3] Initializing TrustworthyDecisionAgent...")
    try:
        rag_agent = TrustworthyDecisionAgent()
        print("[OK] TrustworthyDecisionAgent initialized")
    except Exception as e:
        print(f"[ERROR] Failed to initialize agent: {e}")
        return 1
    
    # Process batch
    print("\n[STEP 4] Processing batch with RAG integration...")
    print("="*80)
    
    successful = 0
    with_citations = 0
    
    for i, user in enumerate(sample_users, 1):
        print(f"\n[{i}/{len(sample_users)}] Processing {user['name']}...")
        
        try:
            # Simulate orchestrator result
            prediction = create_mock_orchestrator_result(user)
            
            # Get trustworthy decision from RAG
            trustworthy_decision = rag_agent.make_trustworthy_decision(prediction, user)
            
            print(f"  Decision: {trustworthy_decision.decision}")
            print(f"  Confidence: {trustworthy_decision.confidence_score*100:.0f}% ({trustworthy_decision.confidence_level.upper()})")
            
            # Check for citations
            if trustworthy_decision.explanation.citations:
                print(f"  Citations: {len(trustworthy_decision.explanation.citations)} sources")
                with_citations += 1
                
                # Print top citation
                top_cite = trustworthy_decision.explanation.citations[0]
                print(f"    - {top_cite.title} ({top_cite.source})")
            else:
                print(f"  Citations: 0 sources [WARNING]")
            
            # Print risk assessment
            risk_lines = trustworthy_decision.risk_assessment.split('\n')
            print(f"  Risk: {risk_lines[0]}")
            
            successful += 1
            
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "="*80)
    print("BATCH SUMMARY")
    print("="*80)
    print(f"Total Processed:        {len(sample_users)}")
    print(f"Successful:             {successful}")
    print(f"With Citations:         {with_citations}")
    print(f"Citation Rate:          {with_citations/successful*100:.0f}%" if successful > 0 else "N/A")
    print("="*80)
    
    # Validation
    print("\n[VALIDATION]")
    if successful >= 4:
        print("[✓] SUCCESS: Processed 4+ users successfully")
    else:
        print(f"[✗] FAILED: Only processed {successful} users (need 4+)")
    
    if with_citations >= 4:
        print("[✓] SUCCESS: Generated citations for 4+ users")
    else:
        print(f"[✗] FAILED: Only generated citations for {with_citations} users (need 4+)")
    
    if successful >= 4 and with_citations >= 4:
        print("\n[SUCCESS] RAG Integration Test PASSED!")
        return 0
    else:
        print("\n[INCOMPLETE] RAG Integration Test Failed")
        return 1


if __name__ == "__main__":
    exit_code = test_rag_integration()
    sys.exit(exit_code)
