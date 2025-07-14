#!/usr/bin/env python3
"""
Test with ALL fields that Clay says it's sending
"""

import requests
import json

API_URL = "https://render-api-tc.onrender.com"

# All fields from Clay template (except Revenue in Last 30 Days)
clay_full_request = {
    "Global Employees": "50",
    "Eligible Employees": "0",
    "Industry": "Retail",
    "Predicted Eligible Employees": "40",
    "Territory": "Micro - Retail",
    "Billing State/Province": "CA",
    "Type": "Employer",
    "Vertical": "Retail & Hospitality",
    "Are they using a Competitor?": "No",
    "Web Technologies": "Wordpress, Google Analytics",
    "Company Payroll Software": "ADP",
    "Marketing Source": "Direct",
    "Strategic Account": "false"
}

print("Testing with ALL fields (as Clay intends to send):")
print(json.dumps(clay_full_request, indent=2))

response = requests.post(f"{API_URL}/predict", json=clay_full_request)
print(f"\nStatus: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    print(f"\nResult:")
    print(f"  Probability: {result['probability_closed_won']}")
    print(f"  Tier: {result['tier']}")
    print(f"  Employee count: {result.get('employee_count', 'N/A')}")
    
    # This should give a different result than the minimal request
    print("\n" + "="*50)
    print("Compare with minimal request (only required fields):")
    
    minimal_request = {
        "Global Employees": "50",
        "Eligible Employees": "0",
        "Industry": "Retail"
    }
    
    response2 = requests.post(f"{API_URL}/predict", json=minimal_request)
    if response2.status_code == 200:
        result2 = response2.json()
        print(f"  Probability: {result2['probability_closed_won']}")
        print(f"  Tier: {result2['tier']}")
        
        if result['tier'] == result2['tier']:
            print("\n⚠️  WARNING: Same tier despite different inputs!")
        else:
            print("\n✅ Different tiers as expected")
else:
    print(f"Error: {response.text}")

# Test what happens with problematic values
print("\n" + "="*50)
print("\nTesting with 'New Payroll' (the problematic value from logs):")

problem_request = {
    "Global Employees": "50",
    "Eligible Employees": "0",
    "Industry": "Retail",
    "Company Payroll Software": "New Payroll",  # This was causing high predictions
    "Territory": "Micro - Retail",
    "Type": "Employer"
}

response3 = requests.post(f"{API_URL}/predict", json=problem_request)
if response3.status_code == 200:
    result3 = response3.json()
    print(f"  Probability: {result3['probability_closed_won']}")
    print(f"  Tier: {result3['tier']}")
    if result3['tier'] == 'A':
        print("  ❌ This is likely the issue - 'New Payroll' causes Tier A!") 