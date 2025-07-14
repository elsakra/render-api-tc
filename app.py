from flask import Flask, request, jsonify, Response
import pandas as pd
import numpy as np
import pickle
import os
import markdown
from markupsafe import Markup
import json
from datetime import datetime
import threading
from collections import deque

app = Flask(__name__)

# Load model at startup
with open('tapcheck_v4_model.pkl', 'rb') as f:
    model = pickle.load(f)

# Initialize logging system
LOG_FILE = 'api_predictions_log.json'
MAX_LOG_SIZE = 10000  # Keep last 10k predictions
prediction_log = deque(maxlen=MAX_LOG_SIZE)
log_lock = threading.Lock()

# Load existing logs on startup
try:
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            existing_logs = json.load(f)
            prediction_log.extend(existing_logs[-MAX_LOG_SIZE:])  # Keep only recent ones
        print(f"Loaded {len(prediction_log)} existing log entries")
except Exception as e:
    print(f"Could not load existing logs: {e}")

def save_logs():
    """Save logs to file"""
    try:
        with log_lock:
            with open(LOG_FILE, 'w') as f:
                json.dump(list(prediction_log), f)
    except Exception as e:
        print(f"Error saving logs: {e}")

def log_prediction(request_data, response_data, employee_count):
    """Log a prediction request and response"""
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'request': {
            'global_employees': request_data.get('Global Employees'),
            'eligible_employees': request_data.get('Eligible Employees'),
            'industry': request_data.get('Industry'),
            'territory': request_data.get('Territory'),
            'type': request_data.get('Type')
        },
        'response': {
            'probability': response_data['probability_closed_won'],
            'tier': response_data['tier'],
            'employee_count': employee_count
        }
    }
    
    with log_lock:
        prediction_log.append(log_entry)
    
    # Save periodically (every 10 predictions)
    if len(prediction_log) % 10 == 0:
        threading.Thread(target=save_logs).start()

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
    
    # For numeric fields, try to convert any value to a number
    if pd.isna(default):  # Numeric field (np.nan as default)
        try:
            # This will handle both actual numbers and string representations of numbers
            # e.g., 100 → 100.0, "100" → 100.0, "100.5" → 100.5
            return float(str_value)
        except (ValueError, TypeError):
            # If conversion fails, return NaN for proper imputation
            return np.nan
    
    # For non-numeric fields, return the original value
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
            'Global Employees': clean_value(data.get('Global Employees'), np.nan),
            'Eligible Employees': clean_value(data.get('Eligible Employees'), np.nan),
            'Predicted Eligible Employees': clean_value(data.get('Predicted Eligible Employees'), np.nan),
            'Revenue in Last 30 Days': clean_value(data.get('Revenue in Last 30 Days'), np.nan),
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
        # Handle NaN values properly
        eligible = features['Eligible Employees']
        global_emp = features['Global Employees']
        
        if pd.notna(eligible):
            employees = eligible
        elif pd.notna(global_emp):
            employees = global_emp
        else:
            employees = 0  # Default if both are missing
        
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
        
        # Get simple explanation factors
        explanation = get_simple_explanation(features, proba, tier)
        
        response_data = {
            'probability_closed_won': round(proba, 4),
            'tier': tier,
            'tier_description': {'A': 'Top 25%', 'B': 'High', 'C': 'Medium', 'D': 'Low'}[tier],
            'employee_count': int(employees),
            'explanation': explanation,
            'status': 'success'
        }
        
        log_prediction(data, response_data, employees)
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'model': 'tapcheck_v4'})

def get_simple_explanation(features, proba, tier):
    """Generate simple list of factors affecting the prediction"""
    
    factors = []
    
    # Employee size
    employees = features.get('Eligible Employees', 0) or features.get('Global Employees', 0)
    if employees > 3000:
        factors.append(f'Large enterprise ({employees:,} employees)')
    elif employees > 1000:
        factors.append(f'Mid-market company ({employees:,} employees)')
    elif employees < 50:
        factors.append(f'Small company ({employees} employees)')
    
    # Industry with win rates
    industry = features.get('Industry', 'missing')
    high_converting = {
        'In-home Personal Care': 74.3,
        'Transportation': 64.5,
        'Healthcare': 43.7,
        'Senior Living': 42.5,
        'Healthcare - Rehabilitation': 43.7,
        'Travel & Tourism': 41.8
    }
    low_converting = {
        'Finance': 5.7,
        'Education': 10.9,
        'Retail': 14.5,
        'Information Technology': 16.0,
        'Insurance': 12.5,
        'Real Estate': 15.8
    }
    
    if industry in high_converting:
        factors.append(f'{industry} industry ({high_converting[industry]:.1f}% historical win rate)')
    elif industry in low_converting:
        factors.append(f'{industry} industry ({low_converting[industry]:.1f}% historical win rate)')
    
    # Payroll software
    payroll = features.get('Company Payroll Software', 'missing')
    excellent_payroll = {
        'Viventium': 81.7,
        'Paychex API': 100.0,
        'NCS': 100.0,
        'QSRSoft Proliant': 89.5,
        'isolved Network': 62.1
    }
    poor_payroll = {
        'New Payroll': 6.0,
        'UKG Pro': 5.4,
        'Workday': 6.9,
        'ADP Vantage HCM': 10.0,
        'Kronos': 15.4
    }
    
    if payroll in excellent_payroll:
        factors.append(f'{payroll} integration ({excellent_payroll[payroll]:.1f}% success rate)')
    elif payroll in poor_payroll:
        factors.append(f'{payroll} integration ({poor_payroll[payroll]:.1f}% success rate)')
    elif payroll == 'ADP':
        factors.append('ADP integration (37.1% win rate)')
    
    # Territory
    territory = features.get('Territory', 'missing')
    if territory == 'missing':
        factors.append('Unassigned territory (48.5% win rate)')
    elif territory == 'Enterprise Territory':
        factors.append('Enterprise territory (11.4% win rate)')
    
    # Strategic account
    if str(features.get('Strategic Account', '')).lower() == 'yes':
        factors.append('Strategic account flag')
    
    # Competitor
    competitor = str(features.get('Are they using a Competitor?', 'missing')).lower()
    if competitor == 'no':
        factors.append('Not using competitor')
    elif competitor == 'yes':
        factors.append('Currently using competitor')
    
    return factors

# Removed get_prediction_explanation - using simplified get_simple_explanation instead

# Removed /predict-with-explanation - consolidated into /predict

@app.route('/analytics/tier-distribution', methods=['GET'])
def tier_distribution():
    """Get current tier distribution from logs"""
    try:
        with log_lock:
            logs = list(prediction_log)
        
        if not logs:
            return jsonify({'error': 'No prediction logs available'}), 404
        
        # Calculate distributions
        total = len(logs)
        tier_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
        
        for log in logs:
            tier = log['response']['tier']
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
        
        # Calculate by employee range
        ranges = {
            '<100': {'min': 0, 'max': 100, 'logs': []},
            '100-299': {'min': 100, 'max': 300, 'logs': []},
            '300-999': {'min': 300, 'max': 1000, 'logs': []},
            '1000-2999': {'min': 1000, 'max': 3000, 'logs': []},
            '>=3000': {'min': 3000, 'max': float('inf'), 'logs': []}
        }
        
        for log in logs:
            emp_count = log['response']['employee_count']
            for range_name, range_info in ranges.items():
                if range_info['min'] <= emp_count < range_info['max']:
                    range_info['logs'].append(log)
                    break
        
        # Analyze each range
        range_analysis = {}
        for range_name, range_info in ranges.items():
            range_logs = range_info['logs']
            if range_logs:
                range_tiers = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
                probs = []
                
                for log in range_logs:
                    tier = log['response']['tier']
                    prob = log['response']['probability']
                    range_tiers[tier] += 1
                    probs.append(prob)
                
                range_analysis[range_name] = {
                    'count': len(range_logs),
                    'tier_distribution': {
                        tier: {
                            'count': count,
                            'percentage': round(count / len(range_logs) * 100, 1)
                        } for tier, count in range_tiers.items()
                    },
                    'probability_stats': {
                        'min': round(min(probs), 4),
                        'max': round(max(probs), 4),
                        'mean': round(sum(probs) / len(probs), 4),
                        'median': round(sorted(probs)[len(probs)//2], 4)
                    }
                }
        
        return jsonify({
            'total_predictions': total,
            'overall_distribution': {
                tier: {
                    'count': count,
                    'percentage': round(count / total * 100, 1)
                } for tier, count in tier_counts.items()
            },
            'by_employee_range': range_analysis,
            'log_period': {
                'oldest': logs[0]['timestamp'] if logs else None,
                'newest': logs[-1]['timestamp'] if logs else None
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analytics/recent-predictions', methods=['GET'])
def recent_predictions():
    """Get recent predictions for debugging"""
    try:
        limit = request.args.get('limit', 100, type=int)
        limit = min(limit, 1000)  # Cap at 1000
        
        with log_lock:
            recent = list(prediction_log)[-limit:]
        
        return jsonify({
            'count': len(recent),
            'predictions': recent
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analytics/probability-quartiles', methods=['GET'])
def probability_quartiles():
    """Calculate current probability quartiles for recalibration"""
    try:
        with log_lock:
            logs = list(prediction_log)
        
        if not logs:
            return jsonify({'error': 'No prediction logs available'}), 404
        
        # Group by employee range
        ranges = {
            '<100': [],
            '100-299': [],
            '300-999': [],
            '1000-2999': [],
            '>=3000': []
        }
        
        for log in logs:
            prob = log['response']['probability']
            emp_count = log['response']['employee_count']
            
            if emp_count < 100:
                ranges['<100'].append(prob)
            elif emp_count < 300:
                ranges['100-299'].append(prob)
            elif emp_count < 1000:
                ranges['300-999'].append(prob)
            elif emp_count < 3000:
                ranges['1000-2999'].append(prob)
            else:
                ranges['>=3000'].append(prob)
        
        # Calculate quartiles for each range
        quartiles = {}
        for range_name, probs in ranges.items():
            if len(probs) >= 4:  # Need at least 4 values for quartiles
                probs_sorted = sorted(probs)
                n = len(probs)
                quartiles[range_name] = {
                    'count': n,
                    'q25': round(probs_sorted[n//4], 4),
                    'q50': round(probs_sorted[n//2], 4),
                    'q75': round(probs_sorted[3*n//4], 4),
                    'current_thresholds': {
                        'A': {'<100': 0.1986, '100-299': 0.2174, '300-999': 0.1479, 
                              '1000-2999': 0.1479, '>=3000': 0.1704}[range_name],
                        'B': {'<100': 0.1249, '100-299': 0.1286, '300-999': 0.0799,
                              '1000-2999': 0.0614, '>=3000': 0.0577}[range_name],
                        'C': {'<100': 0.0577, '100-299': 0.0577, '300-999': 0.0552,
                              '1000-2999': 0.0499, '>=3000': 0.0532}[range_name]
                    },
                    'recommended_thresholds': {
                        'A': probs_sorted[3*n//4],
                        'B': probs_sorted[n//2], 
                        'C': probs_sorted[n//4]
                    }
                }
        
        return jsonify({
            'total_predictions': len(logs),
            'quartiles_by_range': quartiles,
            'recommendation': 'Update tier thresholds to match the recommended values for proper 25% distribution'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 