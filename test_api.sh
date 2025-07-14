#!/bin/bash

# API Base URL
API_URL="https://render-api-tc.onrender.com"

echo "========================================="
echo "Testing Tapcheck API"
echo "========================================="

# Test 1: Health Check
echo -e "\n1. Health Check:"
curl -X GET $API_URL/health
echo -e "\n"

# Test 2: Successful prediction - Small company
echo -e "\n2. Small Company (High probability):"
curl -X POST $API_URL/predict \
  -H "Content-Type: application/json" \
  -d '{
    "Global Employees": 150,
    "Eligible Employees": 120,
    "Industry": "Technology",
    "Territory": "North America",
    "Type": "SMB"
  }' | python3 -m json.tool

# Test 3: Successful prediction - Large enterprise
echo -e "\n3. Large Enterprise:"
curl -X POST $API_URL/predict \
  -H "Content-Type: application/json" \
  -d '{
    "Global Employees": 5000,
    "Eligible Employees": 4500,
    "Industry": "Manufacturing",
    "Predicted Eligible Employees": 4200,
    "Revenue in Last 30 Days": 250000,
    "Territory": "Europe",
    "Billing State/Province": "NY",
    "Type": "Enterprise",
    "Vertical": "Industrial",
    "Are they using a Competitor?": "Yes",
    "Web Technologies": "SAP, Oracle",
    "Company Payroll Software": "Workday",
    "Marketing Source": "Partner",
    "Strategic Account": "Yes"
  }' | python3 -m json.tool

# Test 4: Mid-size company
echo -e "\n4. Mid-size Company:"
curl -X POST $API_URL/predict \
  -H "Content-Type: application/json" \
  -d '{
    "Global Employees": 800,
    "Eligible Employees": 650,
    "Industry": "Healthcare"
  }' | python3 -m json.tool

# Test 5: Error case - missing required field
echo -e "\n5. Error Case - Missing Required Field:"
curl -X POST $API_URL/predict \
  -H "Content-Type: application/json" \
  -d '{
    "Global Employees": 100,
    "Industry": "Retail"
  }' | python3 -m json.tool

echo -e "\n========================================="
echo "Test Complete!"
echo "=========================================" 