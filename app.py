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
import traceback

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

def normalize_field_names(data):
    """Normalize field names to handle both snake_case and Title Case formats"""
    # Mapping from various formats to expected format
    field_mappings = {
        # snake_case to Title Case
        'global_employees': 'Global Employees',
        'eligible_employees': 'Eligible Employees',
        'predicted_eligible_employees': 'Predicted Eligible Employees',
        'revenue_in_last_30_days': 'Revenue in Last 30 Days',
        'territory': 'Territory',
        'industry': 'Industry',
        'billing_state_province': 'Billing State/Province',
        'type': 'Type',
        'vertical': 'Vertical',
        'are_they_using_a_competitor': 'Are they using a Competitor?',
        'web_technologies': 'Web Technologies',
        'company_payroll_software': 'Company Payroll Software',
        'marketing_source': 'Marketing Source',
        'strategic_account': 'Strategic Account',
        # Also handle exact matches (case-insensitive)
        'billing state/province': 'Billing State/Province',
        'are they using a competitor?': 'Are they using a Competitor?',
    }
    
    # Create normalized data dictionary
    normalized = {}
    
    # First, copy over any fields that are already in the correct format
    for key, value in data.items():
        normalized[key] = value
    
    # Then, check for fields that need to be mapped
    for key, value in data.items():
        # Check direct mapping (case-insensitive)
        lower_key = key.lower()
        if lower_key in field_mappings:
            correct_key = field_mappings[lower_key]
            normalized[correct_key] = value
        # Also handle case where it's already correct but different case
        elif key.lower() in [k.lower() for k in field_mappings.values()]:
            # Find the correct casing
            for correct_key in field_mappings.values():
                if key.lower() == correct_key.lower():
                    normalized[correct_key] = value
                    break
    
    return normalized

def save_logs():
    """Save logs to file"""
    try:
        with log_lock:
            with open(LOG_FILE, 'w') as f:
                json.dump(list(prediction_log), f)
    except Exception as e:
        print(f"Error saving logs: {e}")

def log_prediction(request_data, response_data, employee_count, features_dict=None):
    """Log a prediction request and response"""
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'request_from_clay': {
            'global_employees': request_data.get('Global Employees'),
            'eligible_employees': request_data.get('Eligible Employees'),
            'industry': request_data.get('Industry'),
            'territory': request_data.get('Territory'),
            'type': request_data.get('Type')
        },
        'all_features_used': features_dict if features_dict else {},
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

def clean_value(value, default=None, field_name=None):
    """Clean incoming values, treating hyphens as null/missing"""
    # Handle various representations of missing data
    if value is None:
        return default
    
    # Convert to string to check for hyphen patterns
    str_value = str(value).strip()
    
    # Check for hyphen or common missing data indicators
    if str_value in ['-', '--', 'null', 'NULL', 'None', 'none', '']:
        return default
    
    # Special handling for eligible_employees - treat "0" as missing
    if field_name == 'Eligible Employees' and str_value == '0':
        return np.nan
    
    # For numeric fields, try to convert any value to a number
    if pd.isna(default):  # Numeric field (np.nan as default)
        try:
            # Remove commas from numbers (e.g., "10,000" -> "10000")
            clean_str = str_value.replace(',', '')
            return float(clean_str)
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
        
        # Normalize field names to handle both snake_case and Title Case
        data = normalize_field_names(data)
        
        # Check required fields
        required = ['Global Employees', 'Eligible Employees', 'Industry']
        for field in required:
            if field not in data:
                return jsonify({'error': f'Missing: {field}'}), 400
        
        # Prepare features WITHOUT preprocessing - let the model's pipeline handle it
        # The model expects these exact column names in this order
        feature_names = [
            'Territory', 'Industry', 'Billing State/Province', 'Type', 'Vertical',
            'Are they using a Competitor?', 'Web Technologies', 'Company Payroll Software',
            'Marketing Source', 'Strategic Account',
            'Global Employees', 'Eligible Employees', 'Predicted Eligible Employees',
            'Revenue in Last 30 Days'
        ]
        
        # Create raw feature dict - pass exactly what we receive
        features = {}
        for feature in feature_names:
            value = data.get(feature)
            
            # Special handling for Clay's data format
            if isinstance(value, str):
                # Handle Clay's "0" for eligible employees
                if feature == 'Eligible Employees' and value == "0":
                    value = None
                # Handle comma-separated numbers
                elif feature in ['Global Employees', 'Eligible Employees', 'Predicted Eligible Employees', 'Revenue in Last 30 Days']:
                    try:
                        # Remove commas and convert to float
                        value = float(str(value).replace(',', ''))
                    except (ValueError, TypeError):
                        value = None
                # Handle hyphen as missing
                elif value in ['-', '--']:
                    value = None
            
            features[feature] = value
        
        # Create DataFrame with proper column order
        df = pd.DataFrame([features], columns=feature_names)
        
        # Make prediction - model's pipeline will handle imputation and encoding
        proba = model.predict_proba(df)[0][1]
        
        # Determine employee count for tier assignment
        eligible = features.get('Eligible Employees')
        global_emp = features.get('Global Employees')
        
        # Use eligible if available and not None/0, otherwise use global
        if eligible and eligible > 0:
            employees = eligible
        elif global_emp and global_emp > 0:
            employees = global_emp
        else:
            employees = 0
        
        # Assign tier based on employee count and quartiles
        # Use dynamic thresholds based on recent predictions if available
        dynamic_thresholds = get_dynamic_tier_thresholds(employees)
        
        if dynamic_thresholds:
            # Use dynamic thresholds from recent predictions
            tier = assign_tier_dynamic(proba, dynamic_thresholds)
        else:
            # Fall back to original static thresholds
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
        
        # Log with all features that were actually used
        log_prediction(data, response_data, employees, features)
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/predict-raw', methods=['POST'])
def predict_raw():
    """Test endpoint that bypasses Clay-specific preprocessing"""
    try:
        data = request.get_json()
        
        # Normalize field names to handle both snake_case and Title Case
        data = normalize_field_names(data)
        
        # Check required fields
        required = ['Global Employees', 'Eligible Employees', 'Industry']
        for field in required:
            if field not in data:
                return jsonify({'error': f'Missing: {field}'}), 400
        
        # Feature names expected by model
        feature_names = [
            'Territory', 'Industry', 'Billing State/Province', 'Type', 'Vertical',
            'Are they using a Competitor?', 'Web Technologies', 'Company Payroll Software',
            'Marketing Source', 'Strategic Account',
            'Global Employees', 'Eligible Employees', 'Predicted Eligible Employees',
            'Revenue in Last 30 Days'
        ]
        
        # Create raw feature dict - NO PREPROCESSING
        features = {}
        for feature in feature_names:
            if feature in data:
                value = data[feature]
                # Only include if not None
                if value is not None:
                    # For numeric fields, ensure they're numeric
                    if feature in ['Global Employees', 'Eligible Employees', 'Predicted Eligible Employees', 'Revenue in Last 30 Days']:
                        try:
                            features[feature] = float(value)
                        except (ValueError, TypeError):
                            # If can't convert, let model handle it as missing
                            pass
                    else:
                        features[feature] = value
        
        # Create DataFrame with proper column order
        df = pd.DataFrame([features], columns=feature_names)
        
        # Make prediction - model's pipeline will handle everything
        proba = model.predict_proba(df)[0][1]
        
        response_data = {
            'probability_closed_won': round(proba, 4),
            'debug_info': {
                'features_received': len([k for k in data if k in feature_names]),
                'features_used': len(features),
                'numeric_features': {k: v for k, v in features.items() if k in ['Global Employees', 'Eligible Employees']}
            },
            'status': 'success'
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'model': 'tapcheck_v4'})

def get_simple_explanation(features, proba, tier):
    """Generate simple list of factors affecting the prediction"""
    
    factors = []
    
    # Employee size
    employees = features.get('Eligible Employees', 0) or features.get('Global Employees', 0) or 0
    if employees > 3000:
        factors.append(f'Large enterprise ({employees:,.0f} employees)')
    elif employees > 1000:
        factors.append(f'Mid-market company ({employees:,.0f} employees)')
    elif employees < 50 and employees > 0:
        factors.append(f'Small company ({employees:.0f} employees)')
    
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
    
    if payroll and payroll in excellent_payroll:
        factors.append(f'{payroll} integration ({excellent_payroll[payroll]:.1f}% success rate)')
    elif payroll and payroll in poor_payroll:
        factors.append(f'{payroll} integration ({poor_payroll[payroll]:.1f}% success rate)')
    elif payroll == 'ADP':
        factors.append('ADP integration (37.1% win rate)')
    
    # Territory
    territory = features.get('Territory', 'missing')
    if territory == 'missing' or territory is None:
        factors.append('Unassigned territory (48.5% win rate)')
    elif territory == 'Enterprise Territory':
        factors.append('Enterprise territory (11.4% win rate)')
    
    # Strategic account
    strategic = features.get('Strategic Account', '')
    if strategic and str(strategic).lower() == 'yes':
        factors.append('Strategic account flag')
    
    # Competitor
    competitor = features.get('Are they using a Competitor?', 'missing')
    if competitor and str(competitor).lower() == 'no':
        factors.append('Not using competitor')
    elif competitor and str(competitor).lower() == 'yes':
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