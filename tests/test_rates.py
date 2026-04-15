#!/usr/bin/env python3
"""Quick test of RatesAgent"""

from agents.rates_agent import RatesAgent

print("Testing RatesAgent...")
print("-" * 50)

try:
    print("1. Loading RatesAgent...")
    agent = RatesAgent()
    print("   ✓ RatesAgent initialized")
    
    print("\n2. Fetching current rates...")
    rates = agent.get_current_rates()
    print(f"   ✓ Retrieved rates from: {rates['source']}")
    print(f"   ✓ 30-year rate: {rates['rates']['30_year']}%")
    print(f"   ✓ 15-year rate: {rates['rates']['15_year']}%")
    print(f"   ✓ 5/1 ARM rate: {rates['rates']['5_1_arm']}%")
    
    print("\n3. Testing prediction rates...")
    predicted = agent.get_rates_for_prediction("DOWN", 0.80)
    print(f"   ✓ Predicted 30-year (DOWN): {predicted['predicted_rates']['30_year']}%")
    
    print("\n" + "=" * 50)
    print("✓ All RatesAgent tests passed!")
    print("=" * 50)
    
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()
