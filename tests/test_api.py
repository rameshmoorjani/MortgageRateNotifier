#!/usr/bin/env python3
"""
API Testing Script

Quick test suite to verify the REST API is working correctly.
Run this after starting the API with: docker-compose up

Usage:
  python test_api.py [--url http://localhost:8000] [--verbose]
"""

import requests
import json
import time
import sys
import argparse
from typing import Dict, Any

# ANSI Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

class APITester:
    def __init__(self, base_url: str = "http://localhost:8000", verbose: bool = False):
        self.base_url = base_url.rstrip('/')
        self.verbose = verbose
        self.results = {
            'passed': 0,
            'failed': 0,
            'total': 0
        }
        
    def _print(self, message: str, color: str = RESET):
        """Print colored message"""
        print(f"{color}{message}{RESET}")
    
    def _print_section(self, title: str):
        """Print section header"""
        print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
        print(f"{BOLD}{BLUE}{title}{RESET}")
        print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")
    
    def _print_result(self, test_name: str, passed: bool, details: str = ""):
        """Print test result"""
        status = f"{GREEN}✓ PASSED{RESET}" if passed else f"{RED}✗ FAILED{RESET}"
        print(f"  {status}: {test_name}")
        if details and self.verbose:
            print(f"    {details}")
        
        self.results['total'] += 1
        if passed:
            self.results['passed'] += 1
        else:
            self.results['failed'] += 1
    
    def test_connection(self) -> bool:
        """Test basic connection to API"""
        self._print_section("1. Testing Connection")
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            self._print_result("API is reachable", response.status_code == 200)
            return response.status_code == 200
        except requests.exceptions.ConnectionError:
            self._print(f"✗ Cannot connect to {self.base_url}", RED)
            self._print("  Make sure API is running: docker-compose up", YELLOW)
            return False
        except Exception as e:
            self._print(f"✗ Connection error: {e}", RED)
            return False
    
    def test_health_endpoint(self) -> bool:
        """Test /health endpoint"""
        self._print_section("2. Testing Health Endpoint")
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            passed = response.status_code == 200
            self._print_result("Status code 200", passed)
            
            if passed:
                data = response.json()
                
                # Check required fields
                required_fields = ['status', 'rag_system', 'uptime_seconds']
                for field in required_fields:
                    has_field = field in data
                    self._print_result(f"Has '{field}' field", has_field, 
                                      f"Value: {data.get(field)}")
                
                # Check status
                status_ok = data.get('status') == 'healthy'
                self._print_result("Status is 'healthy'", status_ok)
                
                # Check RAG system
                rag_ok = data.get('rag_system') == 'ready'
                self._print_result("RAG system is 'ready'", rag_ok, 
                                  "RAG system needed for decisions")
                
                return status_ok and rag_ok
            return False
            
        except Exception as e:
            self._print_result("Request successful", False, str(e))
            return False
    
    def test_single_decision(self) -> bool:
        """Test /decision endpoint with single user"""
        self._print_section("3. Testing Single Decision Endpoint")
        
        request_data = {
            "user_data": {
                "id": "TEST-USER-001",
                "name": "Test User",
                "email": "test@example.com",
                "current_rate": 4.5,
                "loan_term_years": 30,
                "monthly_payment": 1200,
                "closing_costs": 5500,
                "credit_score": 750,
                "loan_amount": 350000,
                "remaining_term": 240
            },
            "prediction": {
                "predicted_direction": "DOWN",
                "predicted_average_30d": 4.0,
                "min_rate": 3.9,
                "max_rate": 4.1,
                "confidence": 0.82
            },
            "include_full_report": False
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/decision",
                json=request_data,
                timeout=10
            )
            elapsed = (time.time() - start_time) * 1000  # ms
            
            passed = response.status_code == 200
            self._print_result("Status code 200", passed, f"Response time: {elapsed:.0f}ms")
            
            if passed:
                data = response.json()
                
                # Required fields
                required_fields = [
                    'request_id', 'status', 'decision', 'confidence_score',
                    'explanation', 'citations'
                ]
                for field in required_fields:
                    has_field = field in data
                    self._print_result(f"Has '{field}' field", has_field)
                
                # Check decision is valid
                if 'decision' in data:
                    valid_decisions = ['REFINANCE NOW', 'WAIT 1-2 WEEKS', 'WAIT 3+ WEEKS', 
                                     'HOLD YOUR LOAN', 'CONSULT_EXPERT']
                    decision_ok = data['decision'] in valid_decisions
                    self._print_result(f"Decision is valid", decision_ok, 
                                      f"Decision: {data['decision']}")
                
                # Check citations
                if 'citations' in data:
                    citations_ok = len(data['citations']) > 0
                    self._print_result(f"Has citations", citations_ok, 
                                      f"Citations: {len(data['citations'])}")
                
                # Check confidence
                if 'confidence_score' in data:
                    conf = data['confidence_score']
                    conf_ok = 0 <= conf <= 1
                    self._print_result(f"Confidence score valid", conf_ok, 
                                      f"Confidence: {conf*100:.0f}%")
                
                return True
            return False
            
        except requests.exceptions.Timeout:
            self._print_result("Request completed", False, "Request timed out (>10s)")
            return False
        except Exception as e:
            self._print_result("Request successful", False, str(e))
            return False
    
    def test_batch_processing(self) -> bool:
        """Test /batch endpoint"""
        self._print_section("4. Testing Batch Processing Endpoint")
        
        request_data = {
            "users": [
                {
                    "id": "TEST-USER-001",
                    "name": "Test User 1",
                    "current_rate": 4.5,
                    "loan_term_years": 30,
                    "monthly_payment": 1200,
                    "closing_costs": 5500,
                    "credit_score": 750
                },
                {
                    "id": "TEST-USER-002",
                    "name": "Test User 2",
                    "current_rate": 5.0,
                    "loan_term_years": 30,
                    "monthly_payment": 1400,
                    "closing_costs": 6000,
                    "credit_score": 720
                },
                {
                    "id": "TEST-USER-003",
                    "name": "Test User 3",
                    "current_rate": 4.75,
                    "loan_term_years": 30,
                    "monthly_payment": 1300,
                    "closing_costs": 5800,
                    "credit_score": 780
                }
            ],
            "predictions": [
                {
                    "predicted_direction": "DOWN",
                    "predicted_average_30d": 4.0,
                    "min_rate": 3.9,
                    "max_rate": 4.1,
                    "confidence": 0.82
                },
                {
                    "predicted_direction": "DOWN",
                    "predicted_average_30d": 4.0,
                    "min_rate": 3.9,
                    "max_rate": 4.1,
                    "confidence": 0.82
                },
                {
                    "predicted_direction": "UP",
                    "predicted_average_30d": 4.5,
                    "min_rate": 4.4,
                    "max_rate": 4.6,
                    "confidence": 0.75
                }
            ],
            "parallel": False
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/batch",
                json=request_data,
                timeout=20
            )
            elapsed = (time.time() - start_time)
            
            passed = response.status_code == 200
            self._print_result("Status code 200", passed, f"Response time: {elapsed:.1f}s")
            
            if passed:
                data = response.json()
                
                # Check batch fields
                self._print_result("Has 'batch_id' field", 'batch_id' in data)
                self._print_result("Has 'total_users' field", 'total_users' in data)
                self._print_result("Has 'successful' field", 'successful' in data)
                self._print_result("Has 'results' field", 'results' in data)
                
                # Check processing results
                if 'total_users' in data and 'successful' in data:
                    total = data['total_users']
                    success = data['successful']
                    match = total == success
                    self._print_result(f"All users processed", match, 
                                      f"{success}/{total} successful")
                
                # Check individual results
                if 'results' in data:
                    results = data['results']
                    all_successful = all(r.get('status') == 'success' for r in results)
                    self._print_result(f"All results successful", all_successful)
                
                return True
            return False
            
        except requests.exceptions.Timeout:
            self._print_result("Request completed", False, "Request timed out (>20s)")
            return False
        except Exception as e:
            self._print_result("Request successful", False, str(e))
            return False
    
    def test_metrics_endpoint(self) -> bool:
        """Test /metrics endpoint"""
        self._print_section("5. Testing Metrics Endpoint")
        
        try:
            response = requests.get(f"{self.base_url}/metrics", timeout=5)
            passed = response.status_code == 200
            self._print_result("Status code 200", passed)
            
            if passed:
                data = response.json()
                
                # Check fields
                fields = ['timestamp', 'uptime_seconds', 'total_requests', 'status', 'rag_system']
                for field in fields:
                    has_field = field in data
                    self._print_result(f"Has '{field}' field", has_field, 
                                      f"Value: {data.get(field)}")
                
                return True
            return False
            
        except Exception as e:
            self._print_result("Request successful", False, str(e))
            return False
    
    def test_error_handling(self) -> bool:
        """Test error handling"""
        self._print_section("6. Testing Error Handling")
        
        # Test invalid request
        try:
            response = requests.post(
                f"{self.base_url}/decision",
                json={"invalid": "data"},
                timeout=5
            )
            error_handled = response.status_code == 400
            self._print_result("Bad request (400) for invalid data", error_handled, 
                              f"Status: {response.status_code}")
            
            if error_handled and self.verbose:
                self._print(f"    Error: {response.json().get('detail', 'No detail')}", YELLOW)
            
            return error_handled
            
        except Exception as e:
            self._print_result("Error handling works", False, str(e))
            return False
    
    def test_openapi_docs(self) -> bool:
        """Test OpenAPI documentation endpoints"""
        self._print_section("7. Testing API Documentation")
        
        endpoints = [
            ("/docs", "Swagger UI"),
            ("/redoc", "ReDoc"),
            ("/openapi.json", "OpenAPI JSON")
        ]
        
        all_ok = True
        for path, name in endpoints:
            try:
                response = requests.get(f"{self.base_url}{path}", timeout=5)
                ok = response.status_code == 200
                self._print_result(f"{name} ({path})", ok, f"Status: {response.status_code}")
                all_ok = all_ok and ok
            except Exception as e:
                self._print_result(f"{name} ({path})", False, str(e))
                all_ok = False
        
        return all_ok
    
    def run_all_tests(self) -> bool:
        """Run all tests"""
        self._print_section(f"{BOLD}MORTGAGE RATE NOTIFIER - REST API TEST SUITE{RESET}")
        
        # Test connection first
        if not self.test_connection():
            return False
        
        # Run all tests
        self.test_health_endpoint()
        self.test_single_decision()
        self.test_batch_processing()
        self.test_metrics_endpoint()
        self.test_error_handling()
        self.test_openapi_docs()
        
        # Summary
        self._print_section("TEST SUMMARY")
        total = self.results['total']
        passed = self.results['passed']
        failed = self.results['failed']
        
        if failed == 0:
            self._print(f"✓ All {total} tests PASSED!", GREEN)
            self._print(f"\n{BOLD}API is fully functional!{RESET}", BLUE)
            self._print(f"\nNext steps:", BLUE)
            self._print(f"  1. Visit Swagger UI: {self.base_url}/docs", BLUE)
            self._print(f"  2. Try interactive examples", BLUE)
            self._print(f"  3. Integrate with your application", BLUE)
            return True
        else:
            self._print(f"✗ {failed} test(s) FAILED", RED)
            self._print(f"\nPassed: {passed}/{total}", YELLOW)
            self._print(f"Failed: {failed}/{total}", RED)
            self._print(f"\nTroubleshooting tips:", YELLOW)
            self._print(f"  - Check API logs: docker-compose logs api", YELLOW)
            self._print(f"  - Verify OpenAI API key is set", YELLOW)
            self._print(f"  - Ensure RAG system loaded successfully", YELLOW)
            return False


def main():
    parser = argparse.ArgumentParser(
        description='Test the Mortgage Rate Notifier REST API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python test_api.py
  python test_api.py --url http://localhost:8000
  python test_api.py --verbose
  python test_api.py --url http://api.example.com --verbose
        '''
    )
    
    parser.add_argument(
        '--url',
        default='http://localhost:8000',
        help='Base URL of the API (default: http://localhost:8000)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print detailed test information'
    )
    
    args = parser.parse_args()
    
    # Run tests
    tester = APITester(base_url=args.url, verbose=args.verbose)
    success = tester.run_all_tests()
    
    # Exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
