#!/usr/bin/env python3
"""
Test the API with Clay's actual Title Case format
"""

import requests
import json

# Test against deployed API
API_URL = "https://render-api-tc.onrender.com"

def test_clay_actual_format():
    """Test with Clay's actual Title Case format"""
    
    # Clay's actual format based on the template shown
    clay_request = {
        "Global Employees": "50",
        "Eligible Employees": "0", 
        "Industry": "Other",
        "Territory": "Micro - Other",
        "Type": "Employer"
        # Note: Clay only sends these 5 fields
    }
    
    print("Testing Clay's actual Title Case format:")
    print(f"Request: {json.dumps(clay_request, indent=2)}")
    
    response = requests.post(f"{API_URL}/predict", json=clay_request)
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nResponse:")
        print(f"Probability: {result['probability_closed_won']:.4f}")
        print(f"Tier: {result['tier']}")
        print(f"Employee count: {result.get('employee_count', 'N/A')}")
        
        # Check if probability seems inflated
        if result['probability_closed_won'] > 0.5 and clay_request["Eligible Employees"] == "0":
            print("\n⚠️  WARNING: High probability despite 0 eligible employees!")
    else:
        print(f"\nError {response.status_code}: {response.text}")
    
    # Test a few more examples
    test_cases = [
        {
            "Global Employees": "200",
            "Eligible Employees": "0",
            "Industry": "Manufacturing", 
            "Territory": "SMB - Manufacturing",
            "Type": "Employer"
        },
        {
            "Global Employees": "-",  # Hyphen for missing
            "Eligible Employees": "0",
            "Industry": "Other",
            "Territory": "Unknown - Other", 
            "Type": "Employer"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 2):
        print(f"\n{'='*50}")
        print(f"Test {i}: {test_case['Industry']} with {test_case['Global Employees']} employees")
        
        response = requests.post(f"{API_URL}/predict", json=test_case)
        if response.status_code == 200:
            result = response.json()
            print(f"Probability: {result['probability_closed_won']:.4f}")
            print(f"Tier: {result['tier']}")
        else:
            print(f"Error: {response.text}")

if __name__ == "__main__":
    test_clay_actual_format() 