# Main Application Module

import os
import sys
import json
from collections import defaultdict
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS

# Add the parent directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.sec_filings import retrieve_sec_filings
from app.data_enrichment import enrich_sec_filings
from app.market_data import retrieve_market_data, calculate_performance_metrics
from app.logger import app_logger

# Create Flask app with configuration
app = Flask(__name__, template_folder='../templates', static_folder='../static')
CORS(app)  # Enable CORS for all routes
app.config['PROVIDE_AUTOMATIC_OPTIONS'] = True
app.config['DEBUG'] = True

@app.route('/')
def index():
    """
    Render the main index page
    """
    current_year = datetime.now().year
    return render_template('index.html', current_year=current_year)

@app.route('/dashboard')
def dashboard():
    """
    Render the dashboard page with analytics
    """
    try:
        # Retrieve recent filings
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Use a default CIK if no specific CIKs are provided
        default_ciks = ['0000320193', '0000789019']  # Apple and Microsoft as examples
        
        filings = []
        for cik in default_ciks:
            # Remove async/await, use synchronous function call
            cik_filings = retrieve_sec_filings(
                cik,
                years=range(start_date.year, end_date.year + 1)
            )
            filings.extend(cik_filings)
        
        # Remove async/await, use synchronous function call
        enriched_filings = enrich_sec_filings(filings)
        
        return render_template('dashboard.html', filings=enriched_filings)
    
    except Exception as e:
        app_logger.error(f"Dashboard retrieval error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/metrics')
def metrics():
    """
    Render the metrics page with performance analytics
    """
    try:
        # Retrieve all filings from the last year
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        filings = []
        for cik in ['0000320193', '0000789019']:
            cik_filings = retrieve_sec_filings(
                cik,
                years=range(start_date.year, end_date.year + 1)
            )
            filings.extend(cik_filings)
        
        # Enrich filings with market data
        enriched_filings = enrich_sec_filings(filings)
        
        # Calculate performance metrics
        performance_data = []
        for filing in enriched_filings:
            metrics = filing.get('performance_metrics', {})
            if metrics:
                performance_data.append({
                    'company': filing['company_name'],
                    'filing_date': filing['filing_date'],
                    'metrics': metrics
                })
        
        # Calculate average performance
        avg_performance = {
            '7d': 0,
            '30d': 0,
            '182d': 0,
            '365d': 0
        }
        
        if performance_data:
            for period in avg_performance:
                total = sum(p['metrics'].get(period, 0) for p in performance_data)
                avg_performance[period] = total / len(performance_data)
        
        # Get market cap distribution
        market_caps = [f.get('market_cap', 0) for f in enriched_filings if f.get('market_cap')]
        market_cap_dist = {
            'min': min(market_caps) if market_caps else 0,
            'max': max(market_caps) if market_caps else 0,
            'avg': sum(market_caps) / len(market_caps) if market_caps else 0
        }
        
        # Get performance distribution
        performance_dist = defaultdict(list)
        for filing in enriched_filings:
            metrics = filing.get('performance_metrics', {})
            for period, value in metrics.items():
                performance_dist[period].append(value)
        
        # Calculate distribution statistics
        for period in performance_dist:
            values = performance_dist[period]
            if values:
                performance_dist[period] = {
                    'min': min(values),
                    'max': max(values),
                    'avg': sum(values) / len(values)
                }
            else:
                performance_dist[period] = {'min': 0, 'max': 0, 'avg': 0}
        
        # Get top performers
        top_performers = sorted(
            performance_data,
            key=lambda x: x['metrics'].get('30d', 0),
            reverse=True
        )[:10]
        
        app_logger.info('Successfully generated metrics analytics')
        return render_template(
            'metrics.html',
            avg_performance=avg_performance,
            market_cap_dist=market_cap_dist,
            performance_dist=dict(performance_dist),
            top_performers=top_performers
        )
        
    except Exception as e:
        app_logger.error(f'Metrics error: {str(e)}')
        return render_template('error.html', error=str(e))

@app.route('/search', methods=['POST'])
def search():
    """
    Search and analyze SEC filings based on user query
    """
    try:
        data = request.get_json()
        query = data.get('query')
        start_date = data.get('startDate')
        end_date = data.get('endDate')

        if not query:
            return jsonify({'error': 'Search query is required'}), 400

        # Convert dates to years for the filing retrieval
        start_year = datetime.now().year - 1  # Default to last year
        end_year = datetime.now().year
        
        if start_date:
            start_year = datetime.strptime(start_date, '%Y-%m-%d').year
        if end_date:
            end_year = datetime.strptime(end_date, '%Y-%m-%d').year

        # Retrieve CIKs based on query (implement this function)
        def get_ciks_by_query(query):
            """
            Retrieve CIKs for companies matching the query.
            This is a simplified example. For production, use the SEC's API or a database.
            """
            company_cik_mapping = {
                'Apple': '0000320193',
                'Microsoft': '0000789019',
                # Add more companies as needed
            }
            
            ciks = []
            for company, cik in company_cik_mapping.items():
                if query.lower() in company.lower():
                    ciks.append(cik)
            
            return ciks

        # Get CIKs based on the query
        ciks = get_ciks_by_query(query)
        
        if not ciks:
            return jsonify({'error': 'No companies found matching the query'}), 404

        # Retrieve SEC filings
        filings = []
        for cik in ciks:
            cik_filings = retrieve_sec_filings(
                cik,
                forms=['13D', '13G', 'SC 13D', 'SC 13G'],
                years=range(start_year, end_year + 1)
            )
            filings.extend(cik_filings)

        # Enrich filings with market data
        enriched_filings = enrich_sec_filings(filings)

        # Format the response
        formatted_filings = []
        for filing in enriched_filings:
            formatted_filing = {
                'date': filing.get('filing_date', ''),
                'type': filing.get('form', ''),
                'filer': filing.get('filer_name', ''),
                'company': filing.get('company_name', ''),
                'ownership': filing.get('ownership_percentage', 0),
                'market_cap': filing.get('market_cap', 0),
                'performance': filing.get('performance_metrics', {})
            }
            formatted_filings.append(formatted_filing)

        app_logger.info(f'Successfully processed search query: {query}')
        return jsonify({
            'status': 'success',
            'filings': formatted_filings,
            'count': len(formatted_filings)
        })

    except Exception as e:
        app_logger.error(f'Search error: {str(e)}')
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/retrieve_filings', methods=['POST'])
def retrieve_filings():
    """
    Retrieve and process SEC filings
    """
    try:
        # Extract parameters from request
        start_year = request.form.get('start_year', 2009)
        end_year = request.form.get('end_year', datetime.now().year)
        ciks = request.form.getlist('ciks')  # Get the list of CIKs from the request

        if not ciks:
            return jsonify({'error': 'No CIKs provided'}), 400

        # Retrieve SEC filings
        filings = []
        for cik in ciks:
            cik_filings = retrieve_sec_filings(
                cik,
                forms=['13D', '13G', 'SC 13D', 'SC 13G'],
                years=range(int(start_year), int(end_year) + 1)
            )
            filings.extend(cik_filings)
        
        # Enrich filings with market data
        enriched_filings = enrich_sec_filings(filings)
        
        app_logger.info(f'Retrieved and enriched {len(enriched_filings)} filings')
        
        return jsonify({
            'status': 'success',
            'filings': enriched_filings,
            'count': len(enriched_filings)
        })
    
    except Exception as e:
        app_logger.error(f'Filing retrieval error: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/retrieve-data', methods=['POST'])
def retrieve_data():
    """
    Retrieve SEC filings data based on user parameters
    """
    try:
        data = request.get_json()
        start_year = data.get('startYear', 2009)
        end_year = data.get('endYear', datetime.now().year)
        
        # Support both frontend naming conventions
        ciks = data.get('ciks', [])
        
        if not ciks:
            return jsonify({'error': 'No CIKs provided'}), 400

        # Retrieve filings for each CIK
        filings = []
        for cik in ciks:
            cik_filings = retrieve_sec_filings(
                cik,
                forms=['13D', '13G', 'SC 13D', 'SC 13G'],
                years=range(int(start_year), int(end_year) + 1)
            )
            filings.extend(cik_filings)
        
        # Enrich filings with market data
        enriched_filings = enrich_sec_filings(filings)
        
        app_logger.info(f'Retrieved {len(enriched_filings)} filings for {len(ciks)} CIKs')
        
        return jsonify({
            'status': 'success',
            'filings': enriched_filings,
            'count': len(enriched_filings)
        })
    
    except Exception as e:
        app_logger.error(f'Data retrieval error: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/analyze', methods=['POST'])
def analyze_filings():
    """
    Perform advanced analysis on retrieved filings
    """
    try:
        # Extract parameters from request
        filings = request.json.get('filings', [])
        analysis_type = request.json.get('analysis_type', 'basic')
        
        if not filings:
            return jsonify({'error': 'No filings provided for analysis'}), 400
        
        # Retrieve market data for analysis
        symbols = list(set(filing.get('ticker') for filing in filings if filing.get('ticker')))
        market_data = retrieve_market_data(symbols)
        
        # Calculate performance metrics
        performance_metrics = calculate_performance_metrics(market_data)
        
        # Combine filings with market data and performance metrics
        enriched_results = []
        for filing in filings:
            ticker = filing.get('ticker')
            if ticker and ticker in performance_metrics:
                filing['performance_metrics'] = performance_metrics[ticker]
            enriched_results.append(filing)
        
        app_logger.info(f'Completed {analysis_type} analysis for {len(enriched_results)} filings')
        
        return jsonify({
            'status': 'success',
            'results': enriched_results,
            'metrics': performance_metrics
        })
    
    except Exception as e:
        app_logger.error(f'Analysis error: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/display-data', methods=['GET'])
def display_data():
    """
    Render the data display page
    """
    return render_template('data_display.html')

@app.route('/download-data', methods=['POST'])
def download_data():
    """
    Download retrieved SEC filings data
    """
    try:
        data = request.get_json()
        filings = data.get('filings', [])
        
        # Convert to DataFrame for easy export
        import pandas as pd
        df = pd.DataFrame(filings)
        
        # Generate a unique filename
        filename = f'sec_filings_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        filepath = os.path.join('downloads', filename)
        
        # Ensure downloads directory exists
        os.makedirs('downloads', exist_ok=True)
        
        # Save to CSV
        df.to_csv(filepath, index=False)
        
        return jsonify({
            'status': 'success',
            'filename': filename,
            'download_url': f'/downloads/{filename}'
        }), 200
    
    except Exception as e:
        app_logger.error(f'Data download error: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/downloads/<filename>')
def serve_download(filename):
    """
    Serve downloaded files
    """
    return send_file(
        os.path.join('downloads', filename),
        as_attachment=True,
        download_name=filename
    )

def create_app():
    """
    Create and configure the Flask application
    """
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
