#!/usr/bin/env python3
"""
Test and demo script for the RAG (Retrieval-Augmented Generation) system.

This script validates that the trustworthy decision agent is working correctly
and demonstrates the full RAG pipeline with citations and confidence scoring.

Usage:
    python test_rag_system.py
"""

import os
import sys
import importlib.util

def load_rag_modules():
    """Load RAG modules directly, avoiding __init__.py import cascade."""
    # Set a dummy API key to satisfy config imports
    os.environ['OPENAI_API_KEY'] = 'sk-test-key-for-rag-testing'
    
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
    
    return tda_module, rag_module, kb_module


def test_rag_system():
    """Test the RAG system with sample financial data."""
    try:
        print("[STEP 1] Loading RAG modules...")
        tda_module, rag_module, kb_module = load_rag_modules()
        print("[OK] RAG modules loaded successfully\n")
        
        # Initialize agent
        print("[STEP 2] Initializing TrustworthyDecisionAgent...")
        agent = tda_module.TrustworthyDecisionAgent()
        print("[OK] Agent initialized\n")
        
        # Test data - represents Sarah Johnson's mortgage scenario
        print("[STEP 3] Preparing test data...")
        prediction = {
            'predictions': {
                'predicted_direction': 'DOWN',
                'predicted_average_30d': 4.0,
                'min_rate': 3.9,
                'max_rate': 4.1
            },
            'reliability': {'overall_reliability': 0.82},
            'financial_analysis': {
                'current_rate': 4.5,
                'potential_monthly_saving': 250,
                'estimated_closing_costs': 5500,
                'breakeven_months': 22,
                'remaining_loan_term_months': 240,
                'is_financially_safe': True,
                'current_loan_amount': 350000
            }
        }
        
        user_data = {
            'id': 'USER-001',
            'name': 'Sarah Johnson',
            'credit_score': 750
        }
        print("[OK] Test data prepared\n")
        
        # Generate trustworthy decision
        print("[STEP 4] Generating trustworthy decision with RAG...")
        decision = agent.make_trustworthy_decision(prediction, user_data)
        print("[OK] Decision generated\n")
        
        # Print the full report
        print("[STEP 5] Full trustworthy decision report:")
        print("=" * 80)
        report = agent.get_full_report(decision)
        print(report)
        print("=" * 80)
        
        # Print validation summary
        print("\n[VALIDATION SUMMARY]")
        print(f"  - Decision: {decision.decision}")
        print(f"  - Confidence Score: {decision.confidence_score*100:.0f}%")
        print(f"  - Confidence Level: {decision.confidence_level.upper()}")
        print(f"  - Financial Safety: {'Yes' if decision.financial_analysis.get('is_financially_safe') else 'No'}")
        print(f"  - Monthly Savings: ${decision.financial_analysis.get('potential_monthly_saving', 0):.2f}")
        print(f"  - Break-Even: {decision.financial_analysis.get('breakeven_months', 'N/A')} months")
        print(f"  - Citations: {len(decision.explanation.citations)} sources")
        
        print("\n[SUCCESS] RAG system is fully functional!")
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] RAG system test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = test_rag_system()
    sys.exit(exit_code)
