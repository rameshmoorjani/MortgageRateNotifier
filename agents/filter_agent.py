# agents/filter_agent.py
from config import RATE_THRESHOLD, TERMS

def filter_lenders(lenders):
    filtered = []
    for lender in lenders:
        def get_rate(val):
            if isinstance(val, dict):
                # LLM output: expects {'rate': float, ...}
                return val.get('rate')
            return val
        if any(lender.get(term) and isinstance(get_rate(lender[term]), (int, float)) and get_rate(lender[term]) < RATE_THRESHOLD for term in TERMS):
            filtered.append(lender)
    return filtered