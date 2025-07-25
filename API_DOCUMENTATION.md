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

### 2. Prediction with Explanation

Generate a conversion probability prediction for a potential customer with explanation factors.

**Endpoint**: `POST /predict`

**Content-Type**: `application/json`

#### Request Body

**Field Name Formats**: The API accepts field names in both formats:
- **Title Case with spaces**: `"Global Employees"`, `"Eligible Employees"` (original format)
- **snake_case**: `"global_employees"`, `"eligible_employees"` (Clay/integration format)

Both formats work identically. You can even mix formats in the same request.

**Required Fields**:

- `Global Employees` or `global_employees` (integer) - Total number of employees globally
- `Eligible Employees` or `eligible_employees` (integer) - Number of employees eligible for the service
- `Industry` or `industry` (string) - Company's primary industry

**Optional Fields**:

- `Predicted Eligible Employees` or `predicted_eligible_employees` (integer, default: 0) - Estimated eligible employees
- `Revenue in Last 30 Days` or `revenue_in_last_30_days` (integer, default: 0) - Revenue in the last 30 days
- `Territory` or `territory` (string, default: "missing") - Geographic territory
- `Billing State/Province` or `billing_state_province` (string, default: "missing") - Billing location
- `Type` or `type` (string, default: "missing") - Company type (e.g., "Enterprise", "SMB")
- `Vertical` or `vertical` (string, default: "missing") - Business vertical
- `Are they using a Competitor?` or `are_they_using_a_competitor` (string, default: "missing") - Competitor usage status
- `Web Technologies` or `web_technologies` (string, default: "missing") - Technologies used
- `Company Payroll Software` or `company_payroll_software` (string, default: "missing") - Current payroll software
- `Marketing Source` or `marketing_source` (string, default: "missing") - How they heard about us
- `Strategic Account` or `strategic_account` (string, default: "missing") - Strategic account status

#### Hyphen Handling

The API automatically handles hyphens (`-`) as missing values, which is common in Salesforce data exports. The following values are treated as null/missing:
- `-` (single hyphen)
- `--` (double hyphen)
- `null`, `NULL`, `None`, `none`
- Empty strings

For numeric fields, these values will be converted to `NaN` (which allows the model's imputer to use median values). For string fields, they will be converted to `"missing"`.

**Quoted Numbers**: The API intelligently handles quoted numbers in numeric fields. For example:
- `"Predicted Eligible Employees": "100"` → converted to `100`
- `"Predicted Eligible Employees": 100` → remains as `100`
- `"Predicted Eligible Employees": "-"` → converted to `0`

This allows you to safely quote all values in your JSON to handle hyphens without breaking numeric field processing.

**Special handling for required fields**:
- `Global Employees` and `Eligible Employees`: If set to hyphen (`-`), will be converted to `0`
- `Industry`: If set to hyphen (`-`), will be converted to `"Other"`

#### Response

**Success Response** (200 OK):
```json
{
    "probability_closed_won": 0.9865,
    "tier": "A",
    "tier_description": "Top 25%",
    "employee_count": 400,
    "explanation": [
        "Healthcare industry (43.7% historical win rate)",
        "Viventium integration (81.7% success rate)",
        "Not using competitor"
    ],
    "status": "success"
}
```

**Response Fields**:

- `probability_closed_won` (float) - Probability of conversion (0-1)
- `tier` (string)  - Tier classification (A, B, C, or D)
- `tier_description` (string) - Human-readable tier description
- `employee_count` (integer) - Employee count used for classification
- `explanation` (array) - List of factors affecting the prediction
- `status` (string) - Request status

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

### Example 2: Clay Format (snake_case)
```bash
curl -X POST https://render-api-tc.onrender.com/predict \
  -H "Content-Type: application/json" \
  -d '{
    "global_employees": "150",
    "eligible_employees": "120",
    "industry": "Technology",
    "territory": "North America",
    "type": "SMB"
  }'
```

Note: Clay often sends numeric values as strings (e.g., `"150"`). The API handles this automatically.

### Example 3: Full Request
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

### Example 4: Python Request
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

### Example 5: JavaScript/Node.js Request
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

## Analytics Endpoints (New)

The API now includes built-in analytics to monitor tier distributions and diagnose issues.

### 3. Tier Distribution Analysis

Check current tier distribution across all logged predictions.

**Endpoint**: `GET /analytics/tier-distribution`

**Response**:
```json
{
    "total_predictions": 1250,
    "overall_distribution": {
        "A": {"count": 450, "percentage": 36.0},
        "B": {"count": 300, "percentage": 24.0},
        "C": {"count": 300, "percentage": 24.0},
        "D": {"count": 200, "percentage": 16.0}
    },
    "by_employee_range": {
        "<100": {
            "count": 500,
            "tier_distribution": {
                "A": {"count": 200, "percentage": 40.0},
                "B": {"count": 125, "percentage": 25.0},
                "C": {"count": 100, "percentage": 20.0},
                "D": {"count": 75, "percentage": 15.0}
            },
            "probability_stats": {
                "min": 0.0234,
                "max": 0.8765,
                "mean": 0.2345,
                "median": 0.1987
            }
        }
    },
    "log_period": {
        "oldest": "2024-01-15T10:30:00",
        "newest": "2024-01-15T14:45:00"
    }
}
```

### 4. Probability Quartiles

Get current probability quartiles for recalibrating tier thresholds.

**Endpoint**: `GET /analytics/probability-quartiles`

**Response**:
```json
{
    "total_predictions": 1250,
    "quartiles_by_range": {
        "<100": {
            "count": 500,
            "q25": 0.0987,
            "q50": 0.1987,
            "q75": 0.3456,
            "current_thresholds": {
                "A": 0.1986,
                "B": 0.1249,
                "C": 0.0577
            },
            "recommended_thresholds": {
                "A": 0.3456,
                "B": 0.1987,
                "C": 0.0987
            }
        }
    },
    "recommendation": "Update tier thresholds to match the recommended values for proper 25% distribution"
}
```

### 5. Recent Predictions

View recent prediction logs for debugging.

**Endpoint**: `GET /analytics/recent-predictions?limit=100`

**Query Parameters**:
- `limit` (optional, default: 100, max: 1000) - Number of recent predictions to return

**Response**:
```json
{
    "count": 100,
    "predictions": [
        {
            "timestamp": "2024-01-15T14:45:00",
            "request": {
                "global_employees": 150,
                "eligible_employees": 120,
                "industry": "Technology",
                "territory": "West",
                "type": "Enterprise"
            },
            "response": {
                "probability": 0.3456,
                "tier": "A",
                "employee_count": 120
            }
        }
    ]
}
```

## Monitoring Best Practices

1. **Regular Checks**: Monitor `/analytics/tier-distribution` weekly
2. **Alert Threshold**: If Tier A exceeds 35%, recalibration is needed
3. **Recalibration**: Use `/analytics/probability-quartiles` to get new thresholds
4. **Log Retention**: API keeps last 10,000 predictions automatically

---

Last Updated: July 2024 