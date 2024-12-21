import os
import pytest
import sys
import pandas as pd

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(scope='session')
def test_data_dir():
    """
    Fixture to provide a consistent path to test data.
    Allows overriding via environment variable.
    """
    default_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'test_data')
    return os.environ.get('TEST_DATA_PATH', default_path)

@pytest.fixture
def mock_sec_api(mocker):
    """Mock SEC API responses"""
    def mock_get(*args, **kwargs):
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'results': [
                {
                    'cik': '0001234567',
                    'form_type': '13G',
                    'filing_date': '2024-01-15',
                    'shares_owned': 5000000,
                    'percent_of_class': 7.5
                }
            ]
        }
        return mock_response
    
    return mocker.patch('requests.get', side_effect=mock_get)

@pytest.fixture(scope='function')
def mock_market_data(mocker):
    """
    Mock market data retrieval to prevent actual network calls.
    """
    mock_ticker = mocker.MagicMock()
    mock_ticker.history.return_value = pd.DataFrame({
        'Close': [100.0, 105.0, 102.0],
        'Volume': [1000000, 1200000, 950000]
    })
    mock_ticker.info = {
        'currentPrice': 105.0,
        'marketCap': 5000000000,
        'longName': 'Test Company'
    }
    
    return mocker.patch('app.market_data.yf.Ticker', return_value=mock_ticker)
