#!/usr/bin/env python3
"""
Test the API with Clay-formatted data to verify parsing fixes
"""

import requests
import json
import time

API_URL = "https://render-api-tc.onrender.com"

# Test cases with Clay-specific formatting
test_cases = [
    {
        "name": "Large company with comma-separated global employees",
        "data": {
            "eligible_employees": "0",
            "global_employees": "23,196",
            "industry": "Construction",
            "territory": "Enterprise - Other",
            "type": "Employer"
        },
        "expected": {
            "should_use_global": True,
            "employee_count": 23196
        }
    },
    {
        "name": "Company with hyphen for global employees",
        "data": {
            "eligible_employees": "0",
            "global_employees": "-",
            "industry": "Other",
            "territory": "Unknown - Other", 
            "type": "Employer"
        },
        "expected": {
            "should_use_global": False,
            "employee_count": 0
        }
    },
    {
        "name": "Small company with eligible employees as 0",
        "data": {
            "eligible_employees": "0",
            "global_employees": "50",
            "industry": "Other",
            "territory": "Micro - Other",
            "type": "Employer"
        },
        "expected": {
            "should_use_global": True,
            "employee_count": 50
        }
    },
    {
        "name": "Company with actual eligible employees",
        "data": {
            "eligible_employees": "400",
            "global_employees": "500",
            "industry": "Technology",
            "territory": "Mid-Market",
            "type": "Employer"
        },
        "expected": {
            "should_use_global": False,
            "employee_count": 400
        }
    }
]

print("Testing Clay Data Format Parsing")
print("=" * 50)

# Wait for deployment
print("\nWaiting 2 minutes for deployment to complete...")
time.sleep(120)

for i, test in enumerate(test_cases):
    print(f"\nTest {i+1}: {test['name']}")
    print(f"Input: {json.dumps(test['data'], indent=2)}")
    
    response = requests.post(
        f"{API_URL}/predict",
        headers={"Content-Type": "application/json"},
        json=test['data']
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        # Check debug info
        if 'debug' in result:
            debug = result['debug']
            print(f"\nDebug Info:")
            print(f"  Raw inputs: {debug['raw_inputs']}")
            print(f"  Parsed global: {debug['parsed_global_employees']}")
            print(f"  Parsed eligible: {debug['parsed_eligible_employees']}")
            print(f"  Employee count used: {debug['employee_count_used']}")
            
            # Verify expectations
            if debug['employee_count_used'] == test['expected']['employee_count']:
                print(f"  ✓ Employee count correct: {debug['employee_count_used']}")
            else:
                print(f"  ✗ Employee count wrong: expected {test['expected']['employee_count']}, got {debug['employee_count_used']}")
        
        print(f"\nPrediction:")
        print(f"  Probability: {result['probability_closed_won']:.2%}")
        print(f"  Tier: {result['tier']} - {result['tier_description']}")
    else:
        print(f"Error: {response.status_code} - {response.text}")
    
    print("-" * 50)

print("\nTest complete!") 