# Tapcheck Prediction API Documentation

## Overview

The Tapcheck Prediction API provides machine learning-based predictions for customer conversion probability. It analyzes company characteristics and returns a probability score along with a tier classification.

**Base URL**: `https://render-api-tc.onrender.com`

## Authentication

Currently, the API does not require authentication. This may change in future versions.

## Endpoints

### 1. Health Check

Verify the API is running and the model is loaded.

**Endpoint**: `GET /health`

**Response**:
```json
{
    "status": "healthy",
    "model": "tapcheck_v4"
}
```

**Example**:
```bash
curl -X GET https://render-api-tc.onrender.com/health
```

### 2. Prediction

Generate a conversion probability prediction for a potential customer.

**Endpoint**: `POST /predict`

**Content-Type**: `application/json`

#### Request Body

**Required Fields**:

- `Global Employees` (integer)
  - Total number of employees globally
- `Eligible Employees` (integer) 
  - Number of employees eligible for the service
- `Industry` (string)
  - Company's primary industry

**Optional Fields**:

- `Predicted Eligible Employees` (integer, default: 0)
  - Estimated eligible employees
- `Revenue in Last 30 Days` (integer, default: 0)
  - Revenue in the last 30 days
- `Territory` (string, default: "missing")
  - Geographic territory
- `Billing State/Province` (string, default: "missing")
  - Billing location
- `Type` (string, default: "missing")
  - Company type (e.g., "Enterprise", "SMB")
- `Vertical` (string, default: "missing")
  - Business vertical
- `Are they using a Competitor?` (string, default: "missing")
  - Competitor usage status
- `Web Technologies` (string, default: "missing")
  - Technologies used
- `Company Payroll Software` (string, default: "missing")
  - Current payroll software
- `Marketing Source` (string, default: "missing")
  - How they heard about us
- `Strategic Account` (string, default: "missing")
  - Strategic account status

#### Response

**Success Response** (200 OK):
```json
{
    "probability_closed_won": 0.9865,
    "tier": "A",
    "tier_description": "Top 25%",
    "employee_count": 400,
    "status": "success"
}
```

**Response Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `probability_closed_won` | float | Probability of conversion (0-1) |
| `tier` | string | Tier classification (A, B, C, or D) |
| `tier_description` | string | Human-readable tier description |
| `employee_count` | integer | Employee count used for classification |
| `status` | string | Request status |

**Error Response** (400 Bad Request):
```json
{
    "error": "Missing: Eligible Employees"
}
```

## Tier Classification

The API assigns tiers based on employee count and probability thresholds:

### Employee Count < 100
- **Tier A**: Probability > 0.1986 (Top 25%)
- **Tier B**: Probability > 0.1249 (High)
- **Tier C**: Probability > 0.0577 (Medium)
- **Tier D**: Probability ≤ 0.0577 (Low)

### Employee Count 100-299
- **Tier A**: Probability > 0.2174 (Top 25%)
- **Tier B**: Probability > 0.1286 (High)
- **Tier C**: Probability > 0.0577 (Medium)
- **Tier D**: Probability ≤ 0.0577 (Low)

### Employee Count 300-999
- **Tier A**: Probability > 0.1479 (Top 25%)
- **Tier B**: Probability > 0.0799 (High)
- **Tier C**: Probability > 0.0552 (Medium)
- **Tier D**: Probability ≤ 0.0552 (Low)

### Employee Count 1000-2999
- **Tier A**: Probability > 0.1479 (Top 25%)
- **Tier B**: Probability > 0.0614 (High)
- **Tier C**: Probability > 0.0499 (Medium)
- **Tier D**: Probability ≤ 0.0499 (Low)

### Employee Count ≥ 3000
- **Tier A**: Probability > 0.1704 (Top 25%)
- **Tier B**: Probability > 0.0577 (High)
- **Tier C**: Probability > 0.0532 (Medium)
- **Tier D**: Probability ≤ 0.0532 (Low)

## Examples

### Example 1: Minimal Request
```bash
curl -X POST https://render-api-tc.onrender.com/predict \
  -H "Content-Type: application/json" \
  -d '{
    "Global Employees": 150,
    "Eligible Employees": 120,
    "Industry": "Technology"
  }'
```

### Example 2: Full Request
```bash
curl -X POST https://render-api-tc.onrender.com/predict \
  -H "Content-Type: application/json" \
  -d '{
    "Global Employees": 500,
    "Eligible Employees": 400,
    "Industry": "Technology",
    "Predicted Eligible Employees": 380,
    "Revenue in Last 30 Days": 50000,
    "Territory": "North America",
    "Billing State/Province": "CA",
    "Type": "Enterprise",
    "Vertical": "Software",
    "Are they using a Competitor?": "No",
    "Web Technologies": "React, Node.js",
    "Company Payroll Software": "ADP",
    "Marketing Source": "Direct",
    "Strategic Account": "Yes"
  }'
```

### Example 3: Python Request
```python
import requests
import json

url = "https://render-api-tc.onrender.com/predict"
headers = {"Content-Type": "application/json"}

data = {
    "Global Employees": 500,
    "Eligible Employees": 400,
    "Industry": "Technology"
}

response = requests.post(url, headers=headers, json=data)
result = response.json()

print(f"Probability: {result['probability_closed_won']}")
print(f"Tier: {result['tier']} - {result['tier_description']}")
```

### Example 4: JavaScript/Node.js Request
```javascript
const axios = require('axios');

const data = {
    "Global Employees": 500,
    "Eligible Employees": 400,
    "Industry": "Technology"
};

axios.post('https://render-api-tc.onrender.com/predict', data)
    .then(response => {
        console.log('Probability:', response.data.probability_closed_won);
        console.log('Tier:', response.data.tier);
    })
    .catch(error => {
        console.error('Error:', error.response.data);
    });
```

## Error Handling

The API returns appropriate HTTP status codes:

- **200 OK**: Successful prediction
- **400 Bad Request**: Missing required fields or invalid data
- **500 Internal Server Error**: Server-side error

Always check the response status code and handle errors appropriately in your application.

## Rate Limiting

Currently, there are no rate limits implemented. This may change in future versions.

## Support

For issues or questions, please contact the development team or create an issue in the project repository.

## Version

Current API Version: 1.0.0
Model Version: tapcheck_v4

---

Last Updated: July 2024 