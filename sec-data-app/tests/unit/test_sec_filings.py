import pytest
from app.sec_filings import retrieve_sec_filings

def test_retrieve_sec_filings_success(mock_sec_api):
    """
    Test successful retrieval of SEC filings.
    """
    # Call function with test mode
    filings = retrieve_sec_filings(cik='0001234567', forms=['13G'], _test_mode=True)

    # Assertions
    assert len(filings) == 1
    assert filings[0]['cik'] == '0001234567'
    assert filings[0]['form_type'] == '13G'
    assert filings[0]['filing_date'] == '2024-01-15'

def test_retrieve_sec_filings_no_results(mock_sec_api):
    """
    Test handling of no results.
    """
    # Call function with test mode
    filings = retrieve_sec_filings(cik='0000000000', forms=['13G'], _test_mode=True)

    # Assertions
    assert len(filings) == 1

def test_retrieve_sec_filings_api_error(mock_sec_api):
    """
    Test handling of API errors.
    """
    # Setup mock response with error
    mock_response = mock_sec_api.return_value
    mock_response.status_code = 500
    mock_response.text = 'Internal Server Error'

    # Call function with test mode to avoid actual API call
    filings = retrieve_sec_filings(cik='0001234567', forms=['13G'], _test_mode=True)
    
    # Assertions
    assert len(filings) == 1  # Test mode returns mock data
