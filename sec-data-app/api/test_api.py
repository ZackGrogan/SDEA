import os
import sys
import uuid
import json
import click
import pytest
import coverage
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import get_logger

app = Flask(__name__)
logger = get_logger('test_api')

class TestExecutionManager:
    """
    Manages test execution, reporting, and result tracking.
    """
    def __init__(self, base_dir='test_results'):
        """
        Initialize test execution manager.
        
        :param base_dir: Base directory for storing test results
        """
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def generate_test_session_id(self):
        """
        Generate a unique test session ID.
        
        :return: Unique session ID
        """
        return str(uuid.uuid4())

    def run_tests(self, test_type='all', verbose=False, data_path=None, coverage_flag=False, output_format='html'):
        """
        Execute tests with specified parameters.
        
        :param test_type: Type of tests to run
        :param verbose: Enable verbose output
        :param data_path: Custom path for test data
        :param coverage_flag: Generate coverage report
        :param output_format: Format for coverage report
        :return: Test execution results
        """
        session_id = self.generate_test_session_id()
        session_dir = os.path.join(self.base_dir, session_id)
        os.makedirs(session_dir, exist_ok=True)

        logger.info(f"Starting test run: session_id={session_id}, type={test_type}")
        
        # Configure pytest arguments
        pytest_args = ['-v'] if verbose else []
        
        # Select test directories
        if test_type == 'unit':
            pytest_args.extend(['tests/unit'])
        elif test_type == 'integration':
            pytest_args.extend(['tests/integration'])
        elif test_type == 'e2e':
            pytest_args.extend(['tests/e2e'])
        elif test_type == 'performance':
            pytest_args.extend(['tests/performance'])
        else:  # all tests
            pytest_args.extend(['tests'])
        
        # Set custom data path
        if data_path:
            os.environ['TEST_DATA_PATH'] = data_path
        
        # Configure coverage
        cov = None
        if coverage_flag:
            cov = coverage.Coverage(source=['app', 'utils'])
            cov.start()
        
        # Capture test results
        results_file = os.path.join(session_dir, 'test_results.json')
        
        try:
            # Run tests and capture output
            with open(results_file, 'w') as f:
                runner = pytest.main(pytest_args, plugins=[
                    JSONResultPlugin(f)
                ])
            
            # Generate coverage report
            if cov:
                cov.stop()
                cov.save()
                
                coverage_dir = os.path.join(session_dir, 'coverage')
                os.makedirs(coverage_dir, exist_ok=True)
                
                if output_format == 'html':
                    cov.html_report(directory=coverage_dir)
                elif output_format == 'xml':
                    cov.xml_report(outfile=os.path.join(coverage_dir, 'coverage.xml'))
                elif output_format == 'json':
                    cov.json_report(outfile=os.path.join(coverage_dir, 'coverage.json'))
            
            logger.info(f"Test run completed: session_id={session_id}")
            
            return {
                'session_id': session_id,
                'test_type': test_type,
                'status': 'completed',
                'results_file': results_file,
                'exit_code': runner
            }
        
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            return {
                'session_id': session_id,
                'test_type': test_type,
                'status': 'failed',
                'error': str(e)
            }

class JSONResultPlugin:
    """
    Custom pytest plugin to save test results in JSON format.
    """
    def __init__(self, file):
        self.file = file
        self.results = {
            'tests': [],
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'skipped': 0
            }
        }

    def pytest_runtest_logreport(self, report):
        if report.when == 'call':
            test_result = {
                'name': report.nodeid,
                'outcome': report.outcome,
                'duration': report.duration
            }
            self.results['tests'].append(test_result)
            
            if report.outcome == 'passed':
                self.results['summary']['passed'] += 1
            elif report.outcome == 'failed':
                self.results['summary']['failed'] += 1
            elif report.outcome == 'skipped':
                self.results['summary']['skipped'] += 1
            
            self.results['summary']['total'] += 1

    def pytest_sessionfinish(self, session):
        json.dump(self.results, self.file, indent=2)

# Flask API Endpoints
test_manager = TestExecutionManager()

@app.route('/api/tests/run', methods=['POST'])
def handle_run_tests():
    """
    API endpoint to run tests with configurable parameters.
    Enhanced with robust error handling.
    """
    try:
        # Validate JSON input
        data = request.get_json()
        if not data:
            logger.error("Invalid or empty JSON payload received")
            return jsonify({
                "status": "error", 
                "message": "Invalid JSON payload. Please provide test configuration."
            }), 400

        # Validate input parameters
        test_type = data.get('type', 'all')
        valid_test_types = ['unit', 'integration', 'e2e', 'performance', 'all']
        if test_type not in valid_test_types:
            logger.error(f"Invalid test type: {test_type}")
            return jsonify({
                "status": "error", 
                "message": f"Invalid test type. Must be one of {valid_test_types}"
            }), 400

        # Validate data path if provided
        data_path = data.get('data_path')
        if data_path and not os.path.exists(data_path):
            logger.error(f"Invalid data path: {data_path}")
            return jsonify({
                "status": "error", 
                "message": f"Data path does not exist: {data_path}"
            }), 400

        # Execute tests
        result = test_manager.run_tests(
            test_type=test_type,
            verbose=data.get('verbose', False),
            data_path=data_path,
            coverage_flag=data.get('coverage', False),
            output_format=data.get('output_format', 'html')
        )

        logger.info(f"Test run completed: {result}")
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"Unexpected error in test run: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Unexpected server error: {str(e)}'
        }), 500

@app.route('/api/tests/status/<task_id>', methods=['GET'])
def get_test_status(task_id):
    """
    Retrieve the status of a specific test task.
    
    :param task_id: Unique identifier for the test task
    :return: JSON response with task status
    """
    try:
        # Validate task ID
        if not task_id:
            logger.error("No task ID provided")
            return jsonify({
                "status": "error", 
                "message": "Task ID is required"
            }), 400

        # Check if task exists in results directory
        task_dir = os.path.join(test_manager.base_dir, task_id)
        if not os.path.exists(task_dir):
            logger.warning(f"Task not found: {task_id}")
            return jsonify({
                "status": "not_found",
                "message": f"No task found with ID: {task_id}"
            }), 404

        # Retrieve task status
        results_file = os.path.join(task_dir, 'test_results.json')
        if os.path.exists(results_file):
            with open(results_file, 'r') as f:
                task_results = json.load(f)
            
            status = {
                'task_id': task_id,
                'status': 'completed',
                'summary': task_results.get('summary', {}),
                'results_path': results_file
            }
        else:
            status = {
                'task_id': task_id,
                'status': 'in_progress'
            }

        logger.info(f"Status retrieved for task {task_id}")
        return jsonify(status), 200
    
    except Exception as e:
        logger.error(f"Error retrieving test status for {task_id}: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Error retrieving task status: {str(e)}'
        }), 500

@app.route('/api/tests/results/<session_id>', methods=['GET'])
def get_test_results(session_id):
    """
    Retrieve test results for a specific session.
    """
    try:
        results_file = os.path.join(test_manager.base_dir, session_id, 'test_results.json')
        
        if not os.path.exists(results_file):
            return jsonify({
                'status': 'error',
                'message': 'Test results not found'
            }), 404
        
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        return jsonify(results), 200
    
    except Exception as e:
        logger.error(f"Error retrieving test results: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/tests/coverage/<session_id>', methods=['GET'])
def get_coverage_report(session_id):
    """
    Download coverage report for a specific test session.
    """
    try:
        coverage_dir = os.path.join(test_manager.base_dir, session_id, 'coverage')
        
        if not os.path.exists(coverage_dir):
            return jsonify({
                'status': 'error',
                'message': 'Coverage report not found'
            }), 404
        
        # Zip the coverage report for download
        import shutil
        coverage_zip = os.path.join(test_manager.base_dir, session_id, 'coverage.zip')
        shutil.make_archive(coverage_zip[:-4], 'zip', coverage_dir)
        
        return send_file(
            coverage_zip, 
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'coverage_{session_id}.zip'
        )
    
    except Exception as e:
        logger.error(f"Error serving coverage report: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@click.command()
@click.option('--host', default='0.0.0.0', help='Host to bind')
@click.option('--port', default=5001, type=int, help='Port to listen on')
def run_test_api(host, port):
    """
    Run the test execution API server.
    """
    logger.info(f"Starting Test Execution API on {host}:{port}")
    app.run(host=host, port=port, debug=True)

if __name__ == '__main__':
    run_test_api()
