import os
import pytest
import tempfile
from typing import Any, Dict, List

from app.logger import get_logger

logger = get_logger('test_utils')

def generate_mock_sec_filing() -> Dict[str, Any]:
    """
    Generate a mock SEC filing for testing purposes.
    
    Returns:
        Dict containing mock filing data
    """
    return {
        'cik': '0001234567',
        'company_name': 'Test Corporation',
        'filing_type': '13G',
        'filing_date': '2023-01-15',
        'ownership_percentage': 5.5,
        'shares_outstanding': 1000000,
        'market_value': 50000000
    }

def generate_mock_market_data() -> Dict[str, Any]:
    """
    Generate mock market data for testing.
    
    Returns:
        Dict containing mock market data
    """
    return {
        'ticker': 'TEST',
        'current_price': 50.25,
        'market_cap': 5000000000,
        'volume': 1000000,
        'historical_prices': [
            {'date': '2023-01-01', 'price': 45.50},
            {'date': '2023-01-15', 'price': 48.75},
            {'date': '2023-02-01', 'price': 52.00}
        ]
    }

def create_temp_test_directory() -> str:
    """
    Create a temporary directory for test files.
    
    Returns:
        str: Path to the temporary test directory
    """
    try:
        temp_dir = tempfile.mkdtemp(prefix='sec_data_test_')
        logger.info(f"Created temporary test directory: {temp_dir}")
        return temp_dir
    except Exception as e:
        logger.error(f"Failed to create temporary test directory: {e}")
        raise

def cleanup_test_directory(directory: str) -> None:
    """
    Clean up the temporary test directory.
    
    Args:
        directory (str): Path to the directory to clean up
    """
    try:
        import shutil
        if os.path.exists(directory):
            shutil.rmtree(directory)
            logger.info(f"Cleaned up test directory: {directory}")
    except Exception as e:
        logger.error(f"Failed to clean up test directory {directory}: {e}")

def validate_test_data(data: Any, expected_type: type, required_keys: List[str] = None) -> bool:
    """
    Validate test data against expected type and required keys.
    
    Args:
        data (Any): Data to validate
        expected_type (type): Expected type of the data
        required_keys (List[str], optional): List of required keys for dictionaries
    
    Returns:
        bool: True if data is valid, False otherwise
    """
    if not isinstance(data, expected_type):
        logger.warning(f"Data type mismatch. Expected {expected_type}, got {type(data)}")
        return False
    
    if required_keys and isinstance(data, dict):
        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            logger.warning(f"Missing required keys: {missing_keys}")
            return False
    
    return True

@pytest.fixture(scope='session')
def mock_sec_filing():
    """
    Pytest fixture to provide a mock SEC filing.
    
    Returns:
        Dict containing mock filing data
    """
    return generate_mock_sec_filing()

@pytest.fixture(scope='session')
def mock_market_data():
    """
    Pytest fixture to provide mock market data.
    
    Returns:
        Dict containing mock market data
    """
    return generate_mock_market_data()

@pytest.fixture(scope='session')
def temp_test_dir():
    """
    Pytest fixture to create and clean up a temporary test directory.
    
    Yields:
        str: Path to the temporary test directory
    """
    directory = create_temp_test_directory()
    try:
        yield directory
    finally:
        cleanup_test_directory(directory)
