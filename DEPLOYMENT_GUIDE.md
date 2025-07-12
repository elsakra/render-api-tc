# Tapcheck API Deployment Guide

## ✅ Status: Ready for Deployment
- Model retrained with scikit-learn 1.3.0
- Dependencies updated for cloud compatibility
- Local testing successful (probability: 0.997, tier: A)

## 🚀 Quick Deploy Options

### Option 1: Render (Recommended)
1. Visit https://render.com and create account
2. Click "New+" → "Web Service"
3. Connect your GitHub repository
4. Use these settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT app:app`
   - **Environment**: Python 3.9

### Option 2: Railway (Large File Issues)
```bash
railway login
railway up
```
Note: May timeout due to 1.2MB model file size

### Option 3: Heroku
```bash
heroku create tapcheck-api-v4
git push heroku main
```

## 📋 Required Files (All Present)
- ✅ `app.py` - Main Flask API
- ✅ `requirements.txt` - Dependencies (compatible versions)
- ✅ `Procfile` - Heroku config
- ✅ `render.yaml` - Render config
- ✅ `tapcheck_v4_model.pkl` - Trained model (1.2MB)
- ✅ `tapcheck_v4_metadata.json` - Model metadata

## 🔧 API Endpoints
- `GET /health` - Health check
- `POST /predict` - Single prediction

## 📊 Required Input Fields
- `Global Employees` (required)
- `Eligible Employees` (required)
- `Industry` (required)

## 🎯 Sample Request
```bash
curl -X POST YOUR_DEPLOYMENT_URL/predict \
  -H 'Content-Type: application/json' \
  -d '{
    "Global Employees": 250,
    "Eligible Employees": 180,
    "Industry": "Healthcare"
  }'
```

## 📈 Expected Response
```json
{
  "probability_closed_won": 0.997,
  "tier": "A",
  "tier_description": "Top 25%",
  "employee_count": 180,
  "status": "success"
}
```

## 🔍 Tier Thresholds
- **<100 employees**: A > 0.1986, B: 0.1249-0.1986, C: 0.0577-0.1249, D: ≤ 0.0577
- **100-299**: A > 0.2174, B: 0.1286-0.2174, C: 0.0577-0.1286, D: ≤ 0.0577
- **300-999**: A > 0.1479, B: 0.0799-0.1479, C: 0.0552-0.0799, D: ≤ 0.0552
- **1000-2999**: A > 0.1479, B: 0.0614-0.1479, C: 0.0499-0.0614, D: ≤ 0.0499
- **≥3000**: A > 0.1704, B: 0.0577-0.1704, C: 0.0532-0.0577, D: ≤ 0.0532

## 🛠️ Technical Details
- Model: Tapcheck V4 (97.30% ROC-AUC)
- Framework: Flask + scikit-learn 1.3.0
- Dependencies: All pinned to compatible versions
- File size: ~1.2MB (model file)

## 🏆 Next Steps
1. Deploy to Render (recommended)
2. Test with sample request
3. Share public URL with Clay team
4. Monitor performance 