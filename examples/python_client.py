"""
Tapcheck Prediction API Client Example

This example demonstrates how to use the Tapcheck Prediction API
to get conversion probability predictions for potential customers.
"""

import requests
import json
from typing import Dict, Any

class TapcheckAPIClient:
    """Simple client for the Tapcheck Prediction API"""
    
    def __init__(self, base_url: str = "https://render-api-tc.onrender.com"):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}
    
    def health_check(self) -> Dict[str, Any]:
        """Check if the API is healthy"""
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def predict(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a conversion probability prediction
        
        Required fields:
        - Global Employees (int)
        - Eligible Employees (int)
        - Industry (str)
        """
        response = requests.post(
            f"{self.base_url}/predict",
            headers=self.headers,
            json=company_data
        )
        
        if response.status_code != 200:
            raise Exception(f"API Error: {response.json()}")
        
        return response.json()

def main():
    # Initialize the client
    client = TapcheckAPIClient()
    
    # Check API health
    print("Checking API health...")
    health = client.health_check()
    print(f"API Status: {health['status']}, Model: {health['model']}\n")
    
    # Example 1: Small Technology Company
    print("Example 1: Small Technology Company")
    small_tech = {
        "Global Employees": 150,
        "Eligible Employees": 120,
        "Industry": "Technology",
        "Territory": "North America",
        "Type": "SMB"
    }
    result1 = client.predict(small_tech)
    print(f"Probability: {result1['probability_closed_won']:.2%}")
    print(f"Tier: {result1['tier']} - {result1['tier_description']}\n")
    
    # Example 2: Large Manufacturing Company
    print("Example 2: Large Manufacturing Company")
    large_mfg = {
        "Global Employees": 5000,
        "Eligible Employees": 4500,
        "Industry": "Manufacturing",
        "Predicted Eligible Employees": 4200,
        "Revenue in Last 30 Days": 250000,
        "Territory": "Europe",
        "Type": "Enterprise",
        "Vertical": "Industrial",
        "Are they using a Competitor?": "Yes",
        "Company Payroll Software": "Workday",
        "Strategic Account": "Yes"
    }
    result2 = client.predict(large_mfg)
    print(f"Probability: {result2['probability_closed_won']:.2%}")
    print(f"Tier: {result2['tier']} - {result2['tier_description']}\n")
    
    # Example 3: Mid-size Healthcare Company
    print("Example 3: Mid-size Healthcare Company")
    mid_healthcare = {
        "Global Employees": 800,
        "Eligible Employees": 650,
        "Industry": "Healthcare",
        "Billing State/Province": "TX",
        "Marketing Source": "Referral"
    }
    result3 = client.predict(mid_healthcare)
    print(f"Probability: {result3['probability_closed_won']:.2%}")
    print(f"Tier: {result3['tier']} - {result3['tier_description']}\n")

if __name__ == "__main__":
    main() 