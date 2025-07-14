# Tapcheck Prediction API

A machine learning API that predicts customer conversion probability for Tapcheck based on company characteristics.

🔗 **Live API**: https://render-api-tc.onrender.com

📚 **Full Documentation**: [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)

## Overview

This API uses a trained machine learning model to predict the likelihood of a potential customer converting to a Tapcheck client. It analyzes various company attributes and returns a probability score along with a tier classification (A, B, C, or D).

## Quick Start

### Check API Health
```bash
curl https://render-api-tc.onrender.com/health
```

### Make a Prediction
```bash
curl -X POST https://render-api-tc.onrender.com/predict \
  -H "Content-Type: application/json" \
  -d '{
    "Global Employees": 500,
    "Eligible Employees": 400,
    "Industry": "Technology"
  }'
```

### Get Prediction with Explanation (NEW!)
```bash
curl -X POST https://render-api-tc.onrender.com/predict-with-explanation \
  -H "Content-Type: application/json" \
  -d '{
    "Global Employees": 500,
    "Eligible Employees": 400,
    "Industry": "Healthcare",
    "Company Payroll Software": "Viventium"
  }'
```

## Features

- 🚀 Fast prediction response times
- 📊 Probability-based tier classification
- 🔍 Detailed company analysis using 14 features
- 🛡️ Input validation and error handling
- 📈 Based on scikit-learn model (v1.0.2)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Check API status |
| `/predict` | POST | Get conversion prediction |

## Required Fields

- `Global Employees` - Total number of employees
- `Eligible Employees` - Number of eligible employees
- `Industry` - Company's primary industry

## Response Format

```json
{
    "probability_closed_won": 0.9865,
    "tier": "A",
    "tier_description": "Top 25%",
    "employee_count": 400,
    "status": "success"
}
```

## Tier Classification

- **Tier A**: Top 25% probability (Highest conversion likelihood)
- **Tier B**: High probability
- **Tier C**: Medium probability
- **Tier D**: Low probability

## Local Development

### Prerequisites
- Python 3.9.16
- pip

### Installation

1. Clone the repository:
```bash
git clone https://github.com/elsakra/render-api-tc.git
cd render-api-tc
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

The API will be available at `http://localhost:5000`

### Running Tests

```bash
chmod +x test_api.sh
./test_api.sh
```

## Deployment

This API is deployed on Render.com using the provided configuration files:

- `render.yaml` - Render deployment configuration
- `requirements.txt` - Python dependencies
- `.python-version` - Python version specification

### Deploy Your Own Instance

1. Fork this repository
2. Create a new Web Service on [Render.com](https://render.com)
3. Connect your GitHub repository
4. Render will automatically deploy using the configuration

## Technology Stack

- **Framework**: Flask 2.2.5
- **ML Library**: scikit-learn 1.0.2
- **Data Processing**: pandas 1.5.3, numpy 1.23.5
- **Server**: Gunicorn 20.1.0
- **Hosting**: Render.com

## Model Information

- **Model Type**: Machine Learning Classifier
- **Version**: tapcheck_v4
- **Features**: 14 company attributes
- **Output**: Probability score (0-1) and tier classification

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is proprietary and confidential.

## Support

For questions or issues, please create an issue in this repository or contact the development team.

---

**API Status**: ✅ Live and Operational

**Last Updated**: July 2024 