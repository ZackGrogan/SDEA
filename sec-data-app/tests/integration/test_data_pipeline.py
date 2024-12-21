import os
import sys
import pytest
import pandas as pd

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.sec_filings import retrieve_sec_filings
from app.market_data import retrieve_market_data as fetch_market_data
from app.data_enrichment import enrich_sec_filings as enrich_filings_data
from utils.logger import get_logger
from app.data_storage import DataStorage

logger = get_logger('integration_tests')

@pytest.mark.integration
def test_complete_data_pipeline(test_data_dir, mock_sec_api, mock_market_data):
    """
    Integration test for the complete data retrieval and enrichment pipeline.
    """
    # Prepare mock data
    mock_sec_api.return_value.status_code = 200
    mock_sec_api.return_value.json.return_value = {
        'results': [
            {
                'cik': '0001318605',  # Example CIK
                'form_type': '13G',
                'filing_date': '2024-01-15',
                'shares_owned': 5000000,
                'percent_of_class': 7.5
            }
        ]
    }

    # Mock market data
    mock_ticker = mock_market_data.return_value
    mock_ticker.history.return_value = pd.DataFrame({
        'Close': [100.0, 105.0, 102.0],
        'Volume': [1000000, 1200000, 950000]
    })
    mock_ticker.info = {
        'marketCap': 5000000000,
        'sharesOutstanding': 50000000
    }

    # Retrieve SEC filings
    filings = retrieve_sec_filings(cik='0001318605', forms=['13G'])
    assert len(filings) > 0, "No filings retrieved"

    # Fetch market data
    market_data = fetch_market_data(filings[0]['symbol'])
    assert market_data is not None, "Market data retrieval failed"

    # Enrich filings data
    enriched_data = enrich_filings_data(filings, market_data)
    
    # Validate enriched data
    assert 'market_cap' in enriched_data[0], "Market cap not added"
    assert 'stock_price' in enriched_data[0], "Stock price not added"
    assert 'ownership_percentage' in enriched_data[0], "Ownership percentage not calculated"

    logger.info("Data pipeline integration test completed successfully")

@pytest.mark.integration
def test_threshold_tracking(test_data_dir):
    """
    Test threshold exit tracking functionality.
    """
    # Load historical filing data
    historical_data = [
        {
            'cik': '0001318605',
            'filing_date': '2023-01-15',
            'shares_owned': 5000000,
            'percent_of_class': 7.5
        },
        {
            'cik': '0001318605',
            'filing_date': '2024-01-15',
            'shares_owned': 2000000,
            'percent_of_class': 3.0
        }
    ]

    # Check threshold exit
    def check_threshold_exit(filings):
        """
        Determine if a shareholder has fallen below the 5% threshold.
        """
        sorted_filings = sorted(filings, key=lambda x: x['filing_date'])
        
        if len(sorted_filings) < 2:
            return False
        
        latest_filing = sorted_filings[-1]
        previous_filing = sorted_filings[-2]
        
        return (
            previous_filing['percent_of_class'] >= 5.0 and 
            latest_filing['percent_of_class'] < 5.0
        )

    threshold_exit = check_threshold_exit(historical_data)
    assert threshold_exit, "Threshold exit not detected correctly"

    logger.info("Threshold tracking test completed successfully")

@pytest.mark.integration
def test_data_storage_integrity(test_data_dir):
    """Test data storage and retrieval functionality"""
    test_filings = [{
        'cik': '0001318605',
        'form_type': '13G',
        'filing_date': '2024-01-15',
        'shares_owned': 5000000,
        'percent_of_class': 7.5,
        'market_cap': 5000000000,
        'stock_price': 100.0
    }]

    # Save filings
    storage = DataStorage()
    storage.save_filings(test_filings)

    # Retrieve filings
    retrieved_filings = storage.load_filings()

    assert len(retrieved_filings) == len(test_filings)
    assert retrieved_filings[0]['cik'] == test_filings[0]['cik']
    assert retrieved_filings[0]['form_type'] == test_filings[0]['form_type']

    logger.info("Data storage integrity test completed successfully")
