"""
Mortgage Rate Notifier API Client

Simple Python client for interacting with the Mortgage Rate Notifier API.

Install: pip install requests
Usage:
    from mortgage_notifier_client import MortgageNotifierClient
    
    client = MortgageNotifierClient()
    result = client.analyze_decision(
        user_id="USER-001",
        name="John Doe",
        current_rate=4.5,
        loan_term_years=30,
        monthly_payment=1200,
        closing_costs=5500,
        credit_score=750,
        predicted_direction="DOWN",
        predicted_average_30d=4.0,
        confidence=0.82
    )
    print(result['decision']['recommendation'])
"""

import requests
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class MortgageNotifierClient:
    """
    Python client for Mortgage Rate Notifier API
    
    Attributes:
        api_url (str): Base URL for the API
        timeout (int): Request timeout in seconds
        session (requests.Session): Reusable HTTP session
    """
    
    def __init__(
        self, 
        api_url: str = "https://vors6gfapf.execute-api.us-east-1.amazonaws.com/dev",
        timeout: int = 30
    ):
        """
        Initialize the client.
        
        Args:
            api_url: Base URL of the API (default: production endpoint)
            timeout: Request timeout in seconds (default: 30)
        """
        self.api_url = api_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
    
    def health_check(self) -> Dict:
        """
        Check API health status.
        
        Returns:
            dict: Health status including service name and version
            
        Raises:
            requests.RequestException: If request fails
        
        Example:
            >>> client = MortgageNotifierClient()
            >>> health = client.health_check()
            >>> print(health['status'])
            'healthy'
        """
        response = self.session.get(
            f"{self.api_url}/health",
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def get_metrics(self) -> Dict:
        """
        Get API usage metrics and performance statistics.
        
        Returns:
            dict: Metrics including request counts and response times
            
        Raises:
            requests.RequestException: If request fails
        
        Example:
            >>> metrics = client.get_metrics()
            >>> print(f"Total requests: {metrics['total_requests']}")
        """
        response = self.session.get(
            f"{self.api_url}/metrics",
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def analyze_decision(
        self,
        user_id: str,
        name: str,
        current_rate: float,
        loan_term_years: int,
        monthly_payment: float,
        closing_costs: float,
        credit_score: int,
        predicted_direction: str,
        predicted_average_30d: float,
        confidence: float
    ) -> Dict:
        """
        Analyze mortgage refinancing decision for a single user.
        
        Args:
            user_id: Unique user identifier
            name: User's name
            current_rate: Current mortgage rate (%)
            loan_term_years: Loan term in years
            monthly_payment: Monthly payment amount ($)
            closing_costs: Estimated closing costs ($)
            credit_score: Credit score (300-850)
            predicted_direction: Rate direction prediction ("DOWN", "UP", "STABLE")
            predicted_average_30d: Predicted average rate in 30 days (%)
            confidence: Confidence level (0.0 to 1.0)
        
        Returns:
            dict: Decision analysis including recommendation and savings estimate
            
        Raises:
            ValueError: If invalid input parameters
            requests.RequestException: If request fails
        
        Example:
            >>> client = MortgageNotifierClient()
            >>> result = client.analyze_decision(
            ...     user_id="USER-001",
            ...     name="John Doe",
            ...     current_rate=4.5,
            ...     loan_term_years=30,
            ...     monthly_payment=1200,
            ...     closing_costs=5500,
            ...     credit_score=750,
            ...     predicted_direction="DOWN",
            ...     predicted_average_30d=4.0,
            ...     confidence=0.82
            ... )
            >>> print(result['decision']['recommendation'])
            'MARGINAL'
            >>> print(f"${result['decision']['monthly_saving']:.2f}/month")
            '$50.00/month'
        """
        # Validate inputs
        self._validate_decision_inputs(
            current_rate, loan_term_years, monthly_payment, 
            closing_costs, credit_score, predicted_direction, 
            predicted_average_30d, confidence
        )
        
        payload = {
            "user_data": {
                "id": user_id,
                "name": name,
                "current_rate": current_rate,
                "loan_term_years": loan_term_years,
                "monthly_payment": monthly_payment,
                "closing_costs": closing_costs,
                "credit_score": credit_score
            },
            "prediction": {
                "predicted_direction": predicted_direction,
                "predicted_average_30d": predicted_average_30d,
                "confidence": confidence
            }
        }
        
        response = self.session.post(
            f"{self.api_url}/decision",
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def batch_analyze(
        self,
        users: List[Dict]
    ) -> Dict:
        """
        Analyze mortgage decisions for multiple users in one request.
        
        Args:
            users: List of user decision data. Each entry should be a dict with:
                   - "user_data": dict with id, name, current_rate, etc.
                   - "prediction": dict with predicted_direction, etc.
                   Maximum 100 users per request.
        
        Returns:
            dict: Batch results including successful decisions and any errors
            
        Raises:
            ValueError: If >100 users provided
            requests.RequestException: If request fails
        
        Example:
            >>> client = MortgageNotifierClient()
            >>> users = [
            ...     {
            ...         "user_data": {
            ...             "id": "USER-001",
            ...             "name": "Alice",
            ...             "current_rate": 5.5,
            ...             "loan_term_years": 30,
            ...             "monthly_payment": 1500,
            ...             "closing_costs": 5500,
            ...             "credit_score": 780
            ...         },
            ...         "prediction": {
            ...             "predicted_direction": "DOWN",
            ...             "predicted_average_30d": 4.0,
            ...             "confidence": 0.87
            ...         }
            ...     },
            ...     # ... more users
            ... ]
            >>> results = client.batch_analyze(users)
            >>> print(f"Processed: {results['total_processed']}")
            >>> print(f"Successful: {results['successful']}")
        """
        if len(users) > 100:
            raise ValueError("Maximum 100 users per batch request")
        
        response = self.session.post(
            f"{self.api_url}/batch",
            json=users,
            timeout=self.timeout * 3  # Allow longer timeout for batches
        )
        response.raise_for_status()
        return response.json()
    
    def analyze_from_csv(self, csv_path: str) -> List[Dict]:
        """
        Analyze mortgages from a CSV file.
        
        CSV should have columns:
        - id, name, current_rate, loan_term_years, monthly_payment,
          closing_costs, credit_score, predicted_direction,
          predicted_average_30d, confidence
        
        Args:
            csv_path: Path to CSV file
        
        Returns:
            List of decision results
            
        Raises:
            ImportError: If pandas not installed
            FileNotFoundError: If CSV file not found
        
        Example:
            >>> client = MortgageNotifierClient()
            >>> results = client.analyze_from_csv('customers.csv')
            >>> for result in results:
            ...     print(f"{result['user_id']}: {result['decision']['recommendation']}")
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas required for CSV support. Install: pip install pandas")
        
        df = pd.read_csv(csv_path)
        users = df.to_dict('records')
        
        # Convert to API format
        api_users = []
        for user in users:
            api_users.append({
                "user_data": {
                    "id": user['id'],
                    "name": user['name'],
                    "current_rate": user['current_rate'],
                    "loan_term_years": user['loan_term_years'],
                    "monthly_payment": user['monthly_payment'],
                    "closing_costs": user['closing_costs'],
                    "credit_score": user['credit_score']
                },
                "prediction": {
                    "predicted_direction": user['predicted_direction'],
                    "predicted_average_30d": user['predicted_average_30d'],
                    "confidence": user['confidence']
                }
            })
        
        # Process in batches of 100
        all_results = []
        for i in range(0, len(api_users), 100):
            batch = api_users[i:i+100]
            result = self.batch_analyze(batch)
            all_results.extend(result.get('results', []))
        
        return all_results
    
    def export_results_to_csv(
        self,
        results: List[Dict],
        output_path: str
    ) -> None:
        """
        Export decision results to CSV file.
        
        Args:
            results: List of decision results from analyze_decision or batch_analyze
            output_path: Path to write CSV file
            
        Raises:
            ImportError: If pandas not installed
        
        Example:
            >>> client = MortgageNotifierClient()
            >>> results = client.batch_analyze(users)
            >>> client.export_results_to_csv(results['results'], 'decisions.csv')
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas required for CSV export. Install: pip install pandas")
        
        df = pd.DataFrame(results)
        df.to_csv(output_path, index=False)
        print(f"Results exported to {output_path}")
    
    def _validate_decision_inputs(
        self,
        current_rate: float,
        loan_term_years: int,
        monthly_payment: float,
        closing_costs: float,
        credit_score: int,
        predicted_direction: str,
        predicted_average_30d: float,
        confidence: float
    ) -> None:
        """Validate input parameters."""
        if not 2.0 <= current_rate <= 8.0:
            raise ValueError(f"current_rate must be 2.0-8.0, got {current_rate}")
        if not 5 <= loan_term_years <= 40:
            raise ValueError(f"loan_term_years must be 5-40, got {loan_term_years}")
        if monthly_payment <= 0:
            raise ValueError(f"monthly_payment must be positive, got {monthly_payment}")
        if closing_costs < 0:
            raise ValueError(f"closing_costs must be non-negative, got {closing_costs}")
        if not 300 <= credit_score <= 850:
            raise ValueError(f"credit_score must be 300-850, got {credit_score}")
        if predicted_direction not in ("DOWN", "UP", "STABLE"):
            raise ValueError(f"predicted_direction must be DOWN/UP/STABLE, got {predicted_direction}")
        if not 2.0 <= predicted_average_30d <= 8.0:
            raise ValueError(f"predicted_average_30d must be 2.0-8.0, got {predicted_average_30d}")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"confidence must be 0.0-1.0, got {confidence}")


# Example usage
if __name__ == "__main__":
    print("=== Mortgage Rate Notifier API Client ===\n")
    
    # Initialize client
    client = MortgageNotifierClient()
    
    # Check health
    print("1. Health Check:")
    health = client.health_check()
    print(f"   Status: {health['status']}")
    print(f"   Version: {health['version']}\n")
    
    # Get metrics
    print("2. API Metrics:")
    metrics = client.get_metrics()
    print(f"   Total requests: {metrics.get('total_requests', 'N/A')}")
    print(f"   Successful: {metrics.get('successful_decisions', 'N/A')}\n")
    
    # Analyze single decision
    print("3. Single Decision Analysis:")
    result = client.analyze_decision(
        user_id="DEMO-001",
        name="John Doe",
        current_rate=4.5,
        loan_term_years=30,
        monthly_payment=1200,
        closing_costs=5500,
        credit_score=750,
        predicted_direction="DOWN",
        predicted_average_30d=4.0,
        confidence=0.82
    )
    print(f"   User: {result['user_id']}")
    print(f"   Recommendation: {result['decision']['recommendation']}")
    print(f"   Monthly Saving: ${result['decision']['monthly_saving']:.2f}")
    print(f"   Breakeven: {result['decision']['breakeven_months']} months\n")
    
    # Batch analysis
    print("4. Batch Analysis (3 users):")
    users = [
        {
            "user_data": {
                "id": "BATCH-001", "name": "Alice", "current_rate": 5.5,
                "loan_term_years": 30, "monthly_payment": 1500,
                "closing_costs": 5500, "credit_score": 780
            },
            "prediction": {
                "predicted_direction": "DOWN", "predicted_average_30d": 4.0,
                "confidence": 0.87
            }
        },
        {
            "user_data": {
                "id": "BATCH-002", "name": "Bob", "current_rate": 4.5,
                "loan_term_years": 30, "monthly_payment": 1200,
                "closing_costs": 5500, "credit_score": 750
            },
            "prediction": {
                "predicted_direction": "DOWN", "predicted_average_30d": 4.0,
                "confidence": 0.82
            }
        },
        {
            "user_data": {
                "id": "BATCH-003", "name": "Carol", "current_rate": 3.5,
                "loan_term_years": 30, "monthly_payment": 900,
                "closing_costs": 5500, "credit_score": 720
            },
            "prediction": {
                "predicted_direction": "UP", "predicted_average_30d": 4.5,
                "confidence": 0.91
            }
        }
    ]
    
    batch_results = client.batch_analyze(users)
    print(f"   Processed: {batch_results['total_processed']}")
    print(f"   Successful: {batch_results['successful']}")
    print(f"   Failed: {batch_results['failed']}\n")
    
    for result in batch_results['results']:
        print(f"   {result['user_id']}: {result['recommendation']}")
    
    print("\n✅ All examples completed successfully!")
