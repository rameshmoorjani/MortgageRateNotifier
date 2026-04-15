#!/usr/bin/env python3
"""Test RatesAgent with FRED API key"""

import sys
sys.path.insert(0, '.')
from agents.rates_agent import RatesAgent

print('Testing RatesAgent with FRED API key...')
print('=' * 60)

try:
    agent = RatesAgent()
    print('✓ RatesAgent initialized')
    print(f'✓ FRED API key detected: {agent.fred_api_key[:10]}...')
    
    print('')
    print('Fetching current rates...')
    rates = agent.get_current_rates()
    
    print(f'✓ Source: {rates["source"]}')
    print(f'✓ 30-year: {rates["rates"]["30_year"]}%')
    print(f'✓ 15-year: {rates["rates"]["15_year"]}%')
    print(f'✓ 5/1 ARM: {rates["rates"]["5_1_arm"]}%')
    print(f'✓ Confidence: {rates["confidence"]}')
    
    if 'Mock' in rates['source']:
        print('')
        print('⚠️  FRED API returned mock data')
        print('   This may be due to API rate limits or connection issues')
    else:
        print('')
        print('🎉 Real Federal Reserve rates fetched successfully!')
        
except Exception as e:
    print(f'✗ Error: {e}')
    import traceback
    traceback.print_exc()
