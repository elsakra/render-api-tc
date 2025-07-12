from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
import pickle
import os

app = Flask(__name__)

# Load model at startup
with open('tapcheck_v4_model.pkl', 'rb') as f:
    model = pickle.load(f)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        
        # Check required fields
        required = ['Global Employees', 'Eligible Employees', 'Industry']
        for field in required:
            if field not in data:
                return jsonify({'error': f'Missing: {field}'}), 400
        
        # Prepare all 14 features
        features = {
            'Global Employees': data.get('Global Employees', 0),
            'Eligible Employees': data.get('Eligible Employees', 0),
            'Predicted Eligible Employees': data.get('Predicted Eligible Employees', 0),
            'Revenue in Last 30 Days': data.get('Revenue in Last 30 Days', 0),
            'Territory': data.get('Territory', 'missing'),
            'Industry': data.get('Industry', 'missing'),
            'Billing State/Province': data.get('Billing State/Province', 'missing'),
            'Type': data.get('Type', 'missing'),
            'Vertical': data.get('Vertical', 'missing'),
            'Are they using a Competitor?': data.get('Are they using a Competitor?', 'missing'),
            'Web Technologies': data.get('Web Technologies', 'missing'),
            'Company Payroll Software': data.get('Company Payroll Software', 'missing'),
            'Marketing Source': data.get('Marketing Source', 'missing'),
            'Strategic Account': data.get('Strategic Account', 'missing')
        }
        
        # Make prediction
        df = pd.DataFrame([features])
        proba = model.predict_proba(df)[0][1]
        
        # Assign tier based on employee count and quartiles
        employees = features['Eligible Employees'] or features['Global Employees']
        if employees >= 3000:
            tier = 'A' if proba > 0.1704 else 'B' if proba > 0.0577 else 'C' if proba > 0.0532 else 'D'
        elif employees >= 1000:
            tier = 'A' if proba > 0.1479 else 'B' if proba > 0.0614 else 'C' if proba > 0.0499 else 'D'
        elif employees >= 300:
            tier = 'A' if proba > 0.1479 else 'B' if proba > 0.0799 else 'C' if proba > 0.0552 else 'D'
        elif employees >= 100:
            tier = 'A' if proba > 0.2174 else 'B' if proba > 0.1286 else 'C' if proba > 0.0577 else 'D'
        else:
            tier = 'A' if proba > 0.1986 else 'B' if proba > 0.1249 else 'C' if proba > 0.0577 else 'D'
        
        return jsonify({
            'probability_closed_won': round(proba, 4),
            'tier': tier,
            'tier_description': {'A': 'Top 25%', 'B': 'High', 'C': 'Medium', 'D': 'Low'}[tier],
            'employee_count': employees,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'model': 'tapcheck_v4'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 