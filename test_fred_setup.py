#!/usr/bin/env python3
"""Test FRED API integration with environment variable"""

import os
import sys
sys.path.insert(0, '.')

# Test 1: Without FRED key (should use mock)
print("=" * 60)
print("TEST 1: Without FRED_API_KEY (using mock data)")
print("=" * 60)

if 'FRED_API_KEY' in os.environ:
    del os.environ['FRED_API_KEY']

try:
    from agents.rates_agent import RatesAgent
    agent = RatesAgent()
    rates = agent.get_current_rates()
    print(f"✓ Source: {rates['source']}")
    print(f"✓ 30-year: {rates['rates']['30_year']}%")
    print(f"✓ Confidence: {rates['confidence']}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 2: With mock FRED key (to verify environment loading)
print("\n" + "=" * 60)
print("TEST 2: With FRED_API_KEY in environment")
print("=" * 60)

os.environ['FRED_API_KEY'] = 'test_key_12345'

try:
    # Reload the module
    import importlib
    import agents.rates_agent
    importlib.reload(agents.rates_agent)
    
    from agents.rates_agent import RatesAgent
    agent = RatesAgent()
    
    # Check if API key was detected
    if agent.fred_api_key:
        print(f"✓ FRED API key detected: {agent.fred_api_key[:10]}...")
        print("✓ System is configured to use Federal Reserve data")
    else:
        print("✗ FRED API key not loaded from environment")
        
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 60)
print("SETUP COMPLETE")
print("=" * 60)
print("\nNext steps:")
print("1. Get your free FRED API key from: https://stlouisfed.org/apps/fred/")
print("2. Add to .env file: FRED_API_KEY=your_key_here")
print("3. Restart the API server")
print("4. Test: GET http://localhost:8001/rates")
print("\nSee FRED_API_SETUP.md for detailed instructions")
