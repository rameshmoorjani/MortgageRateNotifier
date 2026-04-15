#!/usr/bin/env python3
"""
Rate Limiting Test Script
Test the API's rate limiting functionality

Usage:
    python test_rate_limiting.py
"""

import requests
import time
from datetime import datetime
import sys

BASE_URL = "http://localhost:8001"

def print_header(title):
    """Print a formatted header."""
    print(f"\n{'='*70}")
    print(f"{title:^70}")
    print(f"{'='*70}\n")

def test_endpoint(endpoint, method="GET", data=None, limit=60):
    """
    Test a single endpoint's rate limiting.
    
    Args:
        endpoint: API endpoint path (e.g., "/rates")
        method: HTTP method (GET or POST)
        data: JSON data for POST requests
        limit: Expected requests per minute limit
    """
    
    print_header(f"Testing {method} {endpoint} (Limit: {limit}/min)")
    
    success_count = 0
    rate_limited = False
    rate_limited_at = None
    test_requests = min(limit + 5, 40)  # Don't test too many
    
    print(f"Making {test_requests} requests to find the rate limit...\n")
    
    start_time = time.time()
    
    for request_num in range(test_requests):
        try:
            if method == "GET":
                response = requests.get(
                    f"{BASE_URL}{endpoint}",
                    timeout=5
                )
            else:
                # Default POST data for rate/predict endpoint
                post_data = data or {
                    "prediction_direction": "DOWN",
                    "predicted_average_30d": 4.0,
                    "min_rate": 3.9,
                    "max_rate": 4.1,
                    "confidence": 0.82
                }
                response = requests.post(
                    f"{BASE_URL}{endpoint}",
                    json=post_data,
                    timeout=5
                )
            
            if response.status_code == 200:
                remaining = response.headers.get("X-RateLimit-Remaining", "?")
                limit_header = response.headers.get("X-RateLimit-Limit", "?")
                
                print(f"  ✓ Req {request_num+1:2d}: SUCCESS (200) | "
                      f"Limit: {limit_header} | Remaining: {remaining}")
                success_count += 1
            
            elif response.status_code == 429:
                rate_limited = True
                rate_limited_at = request_num + 1
                retry_after = response.headers.get("Retry-After", "?")
                
                print(f"  ✗ Req {request_num+1:2d}: RATE LIMITED (429) | "
                      f"Retry-After: {retry_after}s")
                print(f"\n🎉 Rate limit triggered at request #{rate_limited_at}!")
                break
            
            else:
                print(f"  ⚠ Req {request_num+1:2d}: Status {response.status_code}")
        
        except requests.exceptions.ConnectionError:
            print(f"\n❌ ERROR: Cannot connect to {BASE_URL}")
            print("   Make sure the API is running:")
            print("   c:\\python314\\python.exe -m uvicorn src.api_server:app --host 0.0.0.0 --port 8001")
            return False
        
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Req {request_num+1:2d}: ERROR - {str(e)}")
        
        time.sleep(0.05)  # 50ms delay between requests
    
    elapsed = time.time() - start_time
    
    # Print summary
    print(f"\n{'─'*70}")
    print(f"Summary:")
    print(f"  ✓ Successful Requests: {success_count}/{test_requests}")
    print(f"  ✗ Rate Limited: {'YES' if rate_limited else 'NO'}")
    if rate_limited_at:
        print(f"  📊 Limited At Request #: {rate_limited_at}")
    print(f"  ⏱️  Time Elapsed: {elapsed:.2f}s")
    print(f"{'─'*70}")
    
    return rate_limited or success_count >= limit


def test_check_api_health():
    """Check if API is running and healthy."""
    print_header("Checking API Health")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ API is running")
            print(f"  Status: {data.get('status', 'unknown')}")
            print(f"  Environment: {data.get('environment', 'unknown')}")
            print(f"  RAG System: {data.get('rag_system', 'unknown')}")
            print(f"  Uptime: {data.get('uptime_seconds', 0):.0f}s")
            return True
        else:
            print(f"✗ API returned status {response.status_code}")
            return False
    
    except requests.exceptions.ConnectionError:
        print(f"✗ Cannot connect to API at {BASE_URL}")
        print("\nTo start the API, run:")
        print("  c:\\python314\\python.exe -m uvicorn src.api_server:app --host 0.0.0.0 --port 8001")
        return False
    
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def main():
    """Run all tests."""
    
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + "🧪 RATE LIMITING TEST SUITE".center(68) + "║")
    print("║" + f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(68) + "║")
    print("╚" + "="*68 + "╝")
    
    # Check API health first
    if not test_check_api_health():
        print("\n❌ API is not running. Cannot proceed with tests.")
        sys.exit(1)
    
    # Test each endpoint
    test_cases = [
        # (endpoint, method, data, limit)
        ("/rates", "GET", None, 100),
        ("/health", "GET", None, 60),
        ("/metrics", "GET", None, 60),
        ("/rates/historical", "GET", None, 50),
        ("/rates/predict", "POST", None, 30),
    ]
    
    results = {}
    
    for endpoint, method, data, limit in test_cases:
        success = test_endpoint(endpoint, method, data, limit)
        results[f"{method} {endpoint}"] = success
    
    # Print final report
    print_header("Final Test Report")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for endpoint, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status} {endpoint}")
    
    print(f"\n{'─'*70}")
    print(f"Overall: {passed}/{total} tests passed")
    print(f"{'─'*70}")
    
    if passed == total:
        print("\n✅ All tests passed! Rate limiting is working correctly.\n")
        return 0
    else:
        print(f"\n⚠️  Some tests failed. Check the output above.\n")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
