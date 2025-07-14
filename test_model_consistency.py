#!/usr/bin/env python3
"""
Test the API to verify it produces the same distribution as the original 77k predictions
"""

import requests
import json
import time
import numpy as np

API_URL = "https://render-api-tc.onrender.com"

# Test cases representing different company sizes from the 77k dataset
test_cases = [
    # Small companies (< 100 employees)
    {
        "name": "Small company 1",
        "data": {
            "Global Employees": "50",
            "Eligible Employees": "40", 
            "Industry": "Retail",
            "Territory": "Micro - Other",
            "Type": "Employer",
            "Company Payroll Software": "ADP",
            "Marketing Source": "Direct"
        }
    },
    {
        "name": "Small company 2",
        "data": {
            "Global Employees": "75",
            "Eligible Employees": "0",  # Clay sends 0 as string
            "Industry": "Healthcare",
            "Territory": "Micro - Healthcare",
            "Type": "Employer"
        }
    },
    # Medium companies (100-999 employees)
    {
        "name": "Medium company 1",
        "data": {
            "Global Employees": "500",
            "Eligible Employees": "400",
            "Industry": "Manufacturing",
            "Territory": "Mid-Market - Manufacturing",
            "Type": "Employer",
            "Company Payroll Software": "Workday",
            "Web Technologies": "Salesforce; Microsoft Office 365"
        }
    },
    {
        "name": "Medium company 2",
        "data": {
            "Global Employees": "250",
            "Eligible Employees": "200",
            "Industry": "Technology",
            "Territory": "Small - Technology",
            "Type": "Employer",
            "Are they using a Competitor?": "No"
        }
    },
    # Large companies (1000+ employees)
    {
        "name": "Large company 1",
        "data": {
            "Global Employees": "5,000",  # With comma
            "Eligible Employees": "0",
            "Industry": "Finance",
            "Territory": "Enterprise - Other",
            "Type": "Employer",
            "Company Payroll Software": "New Payroll"
        }
    },
    {
        "name": "Large company 2",
        "data": {
            "Global Employees": "10,000",
            "Eligible Employees": "8,500",
            "Industry": "Communications",
            "Territory": "Enterprise - Other", 
            "Type": "Employer",
            "Strategic Account": "Yes"
        }
    },
    # Companies with missing data
    {
        "name": "Company with hyphens",
        "data": {
            "Global Employees": "-",
            "Eligible Employees": "0",
            "Industry": "Other",
            "Territory": "Unknown - Other",
            "Type": "Employer"
        }
    },
    {
        "name": "Company with partial data",
        "data": {
            "Global Employees": "300",
            "Eligible Employees": "0",
            "Industry": "Energy"
        }
    }
]

print("Testing Model Consistency with Original 77k Predictions")
print("=" * 60)
print(f"Waiting 2 minutes for deployment...")
time.sleep(120)

# Collect results
results = []
tier_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
probabilities = []

for test in test_cases:
    print(f"\n{test['name']}:")
    print(f"Input: {json.dumps(test['data'], indent=2)}")
    
    response = requests.post(
        f"{API_URL}/predict",
        headers={"Content-Type": "application/json"},
        json=test['data']
    )
    
    if response.status_code == 200:
        result = response.json()
        results.append({
            'name': test['name'],
            'input': test['data'],
            'output': result
        })
        
        tier_counts[result['tier']] += 1
        probabilities.append(result['probability_closed_won'])
        
        print(f"✓ Probability: {result['probability_closed_won']:.4f}")
        print(f"✓ Tier: {result['tier']} - {result['tier_description']}")
        print(f"✓ Employee count used: {result['employee_count']}")
        
        if 'explanation' in result:
            print(f"✓ Factors: {', '.join(result['explanation'][:3])}")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")

# Summary statistics
print("\n" + "=" * 60)
print("SUMMARY STATISTICS")
print("=" * 60)

total = len(results)
print(f"\nTier Distribution (n={total}):")
for tier in ['A', 'B', 'C', 'D']:
    count = tier_counts[tier]
    pct = count / total * 100 if total > 0 else 0
    print(f"  Tier {tier}: {count} ({pct:.1f}%)")

print(f"\nProbability Statistics:")
if probabilities:
    print(f"  Min: {min(probabilities):.4f}")
    print(f"  Max: {max(probabilities):.4f}")
    print(f"  Mean: {np.mean(probabilities):.4f}")
    print(f"  Median: {np.median(probabilities):.4f}")

print("\nExpected vs Actual:")
print("  Expected: ~25% each tier (A/B/C/D)")
print(f"  Actual: A={tier_counts['A']}/{total}, B={tier_counts['B']}/{total}, C={tier_counts['C']}/{total}, D={tier_counts['D']}/{total}")

# Check if distribution is more balanced
a_pct = tier_counts['A'] / total * 100 if total > 0 else 0
if a_pct > 50:
    print("\n⚠️  WARNING: Still too many Tier A predictions!")
    print("   The model preprocessing may still need adjustment.")
else:
    print("\n✅ Distribution looks more balanced!")

print("\nDone!") 