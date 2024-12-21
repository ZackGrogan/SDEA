# Mission: Implement Testing Suite

---

## Step 1: Set up Root Logger (`utils/logger.py`)

**Goal:** Implement the root logger with rotating file handler for centralized logging.

**Tasks:**

- Create a new file `utils/logger.py`.
- Implement the `setup_root_logger` function as described in the documentation, including setting the log level to `DEBUG`, creating a session-based log file, and using `RotatingFileHandler`.
- Ensure the log file permissions are set to `0o600`.
- Add the necessary imports: `logging`, `RotatingFileHandler`, `os`, and `uuid`.
- Add a function to get the root logger.

```python
import logging
from logging.handlers import RotatingFileHandler
import os
import uuid

def setup_root_logger():
    """
    Sets up the root logger with a rotating file handler.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    session_id = uuid.uuid4()
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f'session_{session_id}.log')

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        mode='a'
    )
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    os.chmod(log_file, 0o600)
    return root_logger

def get_root_logger():
    """
    Returns the root logger.
    """
    return logging.getLogger()
```

---

## Step 2: Implement Module-Specific Loggers (`utils/logger.py`)

**Goal:** Implement module-specific loggers that inherit from the root logger.

**Tasks:**

- Open `utils/logger.py`.
- Create functions to get module-specific loggers, such as `get_sec_filings_logger`, `get_market_data_logger`, etc.
- Each module logger should inherit from the root logger.

```python
import logging
from logging.handlers import RotatingFileHandler
import os
import uuid

def setup_root_logger():
    """
    Sets up the root logger with a rotating file handler.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    session_id = uuid.uuid4()
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f'session_{session_id}.log')

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        mode='a'
    )
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    os.chmod(log_file, 0o600)
    return root_logger

def get_root_logger():
    """
    Returns the root logger.
    """
    return logging.getLogger()

def get_sec_filings_logger():
    """
    Returns the logger for the SEC filings module.
    """
    return logging.getLogger('sec_filings_logger')

def get_market_data_logger():
    """
    Returns the logger for the market data module.
    """
    return logging.getLogger('market_data_logger')

def get_data_parsing_logger():
    """
    Returns the logger for the data parsing module.
    """
    return logging.getLogger('data_parsing_logger')

def get_data_enrichment_logger():
    """
    Returns the logger for the data enrichment module.
    """
    return logging.getLogger('data_enrichment_logger')

def get_threshold_tracking_logger():
    """
    Returns the logger for the threshold tracking module.
    """
    return logging.getLogger('threshold_tracking_logger')

def get_data_storage_logger():
    """
    Returns the logger for the data storage module.
    """
    return logging.getLogger('data_storage_logger')

def get_frontend_logger():
    """
    Returns the logger for the frontend.
    """
    return logging.getLogger('frontend_logger')

def get_backend_logger():
    """
    Returns the logger for the backend.
    """
    return logging.getLogger('backend_logger')
```

---

## Step 3: Implement CLI Test Command (`cli.py`)

**Goal:** Implement the CLI test command with options for test type, verbosity, data path, coverage, and output format.

**Tasks:**

- Open `cli.py`.
- Add the `test` command using `click`, including options for `type`, `verbose`, `data_path`, `coverage`, and `output_format`.
- Implement the logic to initialize the root logger if it hasn't been initialized yet.
- Add a placeholder for test execution logic.
- Add the necessary imports: `click` and `logging`.
- Import `setup_root_logger` and `get_root_logger` from `utils/logger.py`.

```python
import click
import logging
from utils.logger import setup_root_logger, get_root_logger

@click.group()
def cli():
    """SEC Data Testing Suite CLI"""
    pass

@cli.command()
@click.option('--type', type=click.Choice(['unit', 'integration', 'e2e', 'performance', 'all']), required=True, help="Type of test to run")
@click.option('--verbose', is_flag=True, help="Increase output verbosity")
@click.option('--data-path', type=click.Path(exists=True), default='data/test_data', help="Path to custom test data directory")
@click.option('--coverage', is_flag=True, help="Generate code coverage reports")
@click.option('--output-format', type=click.Choice(['html', 'xml', 'json']), default='html', help="Specify report format")
def test(type, verbose, data_path, coverage, output_format):
    """Run specified test suite"""
    root_logger = get_root_logger()
    if not root_logger.hasHandlers():
        setup_root_logger()
    
    # Placeholder for test execution logic
    print(f"Running {type} tests with verbose: {verbose}, data path: {data_path}, coverage: {coverage}, output format: {output_format}")

if __name__ == '__main__':
    cli()
```

---

## Step 4: Implement Test Execution Endpoint (`api/api_utils.py`)

**Goal:** Create the `/api/tests/run` endpoint to handle test execution requests.

**Tasks:**

- Open `api/api_utils.py`.
- Add a function `run_tests` that will handle the test execution logic.
- Use `subprocess.Popen` to execute CLI commands.
- Implement asynchronous task handling using `threading`.
- Log the start and end of the test execution.
- Add the necessary imports: `subprocess`, `logging`, `json`, `os`, `shlex`, and `threading`.
- Import `get_root_logger` from `utils/logger.py`.

```python
import subprocess
import logging
import json
import os
import shlex
import threading
from utils.logger import get_root_logger

def run_tests(test_type, verbose, data_path, coverage, output_format):
    """
    Executes the specified test suite using the CLI.
    """
    logger = get_root_logger()
    logger.info(f"Starting test execution for type: {test_type}")
    try:
        command = ["python", "cli.py", "test", "--type", test_type]
        if verbose:
            command.append("--verbose")
        command.extend(["--data-path", data_path])
        if coverage:
            command.append("--coverage")
        command.extend(["--output-format", output_format])
        
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            logger.info(f"Test execution successful for type: {test_type}")
            result = {"status": "success", "output": stdout}
        else:
            logger.error(f"Test execution failed for type: {test_type}, error: {stderr}")
            result = {"status": "error", "output": stderr}
        logger.info(f"Finished test execution for type: {test_type}")
        return result

    except Exception as e:
        logger.exception(f"An error occurred during test execution: {e}")
        return {"status": "error", "output": str(e)}
```

---

## Step 5: Integrate Test Execution Endpoint with Flask App (`app.py`)

**Goal:** Integrate the `run_tests` function with the Flask application.

**Tasks:**

- Open `app.py`.
- Import `run_tests` from `api/api_utils.py`.
- Add a route `/api/tests/run` that accepts `POST` requests.
- Extract the test parameters from the request body.
- Call the `run_tests` function with the extracted parameters in a separate thread.
- Return a success message with a task ID.
- Implement a mechanism to track the status of the test execution using the task ID.
- Add the necessary imports: `Flask`, `request`, `jsonify`, `threading`, and `uuid`.

```python
from flask import Flask, request, jsonify
from api.api_utils import run_tests
import threading
import uuid

app = Flask(__name__)

test_tasks = {}

@app.route('/api/tests/run', methods=['POST'])
def handle_run_tests():
    """
    Handles the test execution request.
    """
    data = request.get_json()
    test_type = data.get('type')
    verbose = data.get('verbose', False)
    data_path = data.get('data_path', 'data/test_data')
    coverage = data.get('coverage', False)
    output_format = data.get('output_format', 'html')

    task_id = str(uuid.uuid4())
    test_tasks[task_id] = {"status": "running"}

    def run_test_task():
        result = run_tests(test_type, verbose, data_path, coverage, output_format)
        test_tasks[task_id] = result

    thread = threading.Thread(target=run_test_task)
    thread.start()
    
    return jsonify({"status": "success", "task_id": task_id})

@app.route('/api/tests/status/<task_id>', methods=['GET'])
def get_test_status(task_id):
    """
    Retrieves the status of a test execution task.
    """
    if task_id in test_tasks:
        return jsonify(test_tasks[task_id])
    else:
        return jsonify({"status": "error", "message": "Task not found."}), 404

if __name__ == '__main__':
    app.run(debug=True)
```

---

## Step 6: Implement Log Retrieval Endpoint (`api/api_utils.py`)

**Goal:** Create the `/api/logs/get` endpoint to retrieve log files.

**Tasks:**

- Open `api/api_utils.py`.
- Add a function `get_logs` that will handle the log retrieval logic.
- Implement the logic to read the latest log file.
- Return the log content as a JSON response.
- Add the necessary imports: `os`, `glob`, and `json`.
- Import `get_root_logger` from `utils/logger.py`.

```python
import subprocess
import logging
import json
import os
import shlex
import threading
import glob
from utils.logger import get_root_logger

def run_tests(test_type, verbose, data_path, coverage, output_format):
    """
    Executes the specified test suite using the CLI.
    """
    logger = get_root_logger()
    logger.info(f"Starting test execution for type: {test_type}")
    try:
        command = ["python", "cli.py", "test", "--type", test_type]
        if verbose:
            command.append("--verbose")
        command.extend(["--data-path", data_path])
        if coverage:
            command.append("--coverage")
        command.extend(["--output-format", output_format])
        
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            logger.info(f"Test execution successful for type: {test_type}")
            result = {"status": "success", "output": stdout}
        else:
            logger.error(f"Test execution failed for type: {test_type}, error: {stderr}")
            result = {"status": "error", "output": stderr}
        logger.info(f"Finished test execution for type: {test_type}")
        return result

    except Exception as e:
        logger.exception(f"An error occurred during test execution: {e}")
        return {"status": "error", "output": str(e)}

def get_logs():
    """
    Retrieves the content of the latest log file.
    """
    logger = get_root_logger()
    log_dir = 'logs'
    try:
        log_files = glob.glob(os.path.join(log_dir, 'session_*.log'))
        if not log_files:
            return {"status": "error", "message": "No log files found."}
        latest_log_file = max(log_files, key=os.path.getctime)
        with open(latest_log_file, 'r') as f:
            log_content = f.read()
        return {"status": "success", "log_content": log_content}
    except Exception as e:
        logger.exception(f"An error occurred while retrieving logs: {e}")
        return {"status": "error", "message": str(e)}
```

---

## Step 7: Integrate Log Retrieval Endpoint with Flask App (`app.py`)

**Goal:** Integrate the `get_logs` function with the Flask application.

**Tasks:**

- Open `app.py`.
- Import `get_logs` from `api/api_utils.py`.
- Add a route `/api/logs/get` that accepts `GET` requests.
- Call the `get_logs` function.
- Return the result as a JSON response.
