#!/usr/bin/env python3
"""Test RatesAgent"""
import sys
sys.path.insert(0, '.')

try:
    print("Testing RatesAgent initialization...")
    from agents.rates_agent import RatesAgent
    agent = RatesAgent()
    print("✓ RatesAgent initialized successfully")
    
    print("\nFetching current rates...")
    rates = agent.get_current_rates()
    print(f"✓ 30-year rate: {rates['rates']['30_year']}%")
    print(f"✓ 15-year rate: {rates['rates']['15_year']}%")
    print(f"✓ 5/1 ARM rate: {rates['rates']['5_1_arm']}%")
    print(f"✓ Source: {rates['source']}")
    
    print("\n✓ All tests passed!")
    
except Exception as e:
    print(f"✗ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
