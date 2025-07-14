from flask import Flask, request, jsonify, Response
import pandas as pd
import numpy as np
import pickle
import os
import markdown
from markupsafe import Markup

app = Flask(__name__)

# Load model at startup
with open('tapcheck_v4_model.pkl', 'rb') as f:
    model = pickle.load(f)

def clean_value(value, default=None):
    """Clean incoming values, treating hyphens as null/missing"""
    # Handle various representations of missing data
    if value is None:
        return default
    
    # Convert to string to check for hyphen patterns
    str_value = str(value).strip()
    
    # Check for hyphen or common missing data indicators
    if str_value in ['-', '--', 'null', 'NULL', 'None', 'none', '']:
        return default
    
    # For numeric fields, also check if it's a valid number
    if default == 0:  # Numeric field
        try:
            # Try to convert to number, but still check for hyphen first
            if str_value == '-':
                return default
            return float(str_value)
        except (ValueError, TypeError):
            return default
    
    return value

def render_markdown_as_html(markdown_file):
    """Convert markdown file to HTML with styling"""
    try:
        with open(markdown_file, 'r') as f:
            content = f.read()
        
        # Convert markdown to HTML
        html_content = markdown.markdown(content, extensions=['tables', 'fenced_code', 'codehilite'])
        
        # Wrap in HTML template with styling
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Tapcheck Prediction API Documentation</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1000px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .content {{
                    background-color: white;
                    padding: 40px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                h1, h2, h3, h4 {{
                    color: #2c3e50;
                    margin-top: 30px;
                }}
                h1 {{
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 10px;
                }}
                h2 {{
                    border-bottom: 1px solid #e0e0e0;
                    padding-bottom: 8px;
                }}
                code {{
                    background-color: #f4f4f4;
                    padding: 2px 4px;
                    border-radius: 3px;
                    font-family: 'Consolas', 'Monaco', monospace;
                }}
                pre {{
                    background-color: #f8f8f8;
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                    padding: 15px;
                    overflow-x: auto;
                }}
                pre code {{
                    background-color: transparent;
                    padding: 0;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 20px 0;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f2f2;
                    font-weight: bold;
                }}
                tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                a {{
                    color: #3498db;
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
                .nav {{
                    margin-bottom: 30px;
                    padding: 15px;
                    background-color: #ecf0f1;
                    border-radius: 4px;
                }}
                .nav a {{
                    margin-right: 20px;
                    font-weight: 500;
                }}
                .footer {{
                    margin-top: 50px;
                    padding-top: 20px;
                    border-top: 1px solid #e0e0e0;
                    text-align: center;
                    color: #666;
                    font-size: 0.9em;
                }}
            </style>
        </head>
        <body>
            <div class="content">
                <div class="nav">
                    <a href="/">Home</a>
                    <a href="/docs">API Documentation</a>
                    <a href="/docs/openapi">OpenAPI Spec</a>
                    <a href="/health">Health Check</a>
                </div>
                {html_content}
                <div class="footer">
                    Tapcheck Prediction API | <a href="https://render-api-tc.onrender.com">https://render-api-tc.onrender.com</a>
                </div>
            </div>
        </body>
        </html>
        """
        return html_template
    except Exception as e:
        return f"<h1>Error loading documentation</h1><p>{str(e)}</p>"

@app.route('/')
def index():
    """Serve the README as the landing page"""
    return render_markdown_as_html('README.md')

@app.route('/docs')
def docs():
    """Serve the full API documentation"""
    return render_markdown_as_html('API_DOCUMENTATION.md')

@app.route('/docs/openapi')
def openapi_spec():
    """Serve the OpenAPI specification"""
    try:
        with open('openapi.yaml', 'r') as f:
            content = f.read()
        return Response(content, mimetype='text/yaml')
    except:
        return jsonify({'error': 'OpenAPI spec not found'}), 404

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        
        # Check required fields
        required = ['Global Employees', 'Eligible Employees', 'Industry']
        for field in required:
            if field not in data:
                return jsonify({'error': f'Missing: {field}'}), 400
        
        # Prepare all 14 features with hyphen handling
        features = {
            'Global Employees': clean_value(data.get('Global Employees'), 0),
            'Eligible Employees': clean_value(data.get('Eligible Employees'), 0),
            'Predicted Eligible Employees': clean_value(data.get('Predicted Eligible Employees'), 0),
            'Revenue in Last 30 Days': clean_value(data.get('Revenue in Last 30 Days'), 0),
            'Territory': clean_value(data.get('Territory'), 'missing'),
            'Industry': clean_value(data.get('Industry'), 'Other') if data.get('Industry') == '-' else data.get('Industry', 'missing'),
            'Billing State/Province': clean_value(data.get('Billing State/Province'), 'missing'),
            'Type': clean_value(data.get('Type'), 'missing'),
            'Vertical': clean_value(data.get('Vertical'), 'missing'),
            'Are they using a Competitor?': clean_value(data.get('Are they using a Competitor?'), 'missing'),
            'Web Technologies': clean_value(data.get('Web Technologies'), 'missing'),
            'Company Payroll Software': clean_value(data.get('Company Payroll Software'), 'missing'),
            'Marketing Source': clean_value(data.get('Marketing Source'), 'missing'),
            'Strategic Account': clean_value(data.get('Strategic Account'), 'missing')
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