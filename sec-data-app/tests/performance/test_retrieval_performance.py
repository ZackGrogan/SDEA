import os
import sys
import time
import pytest
import memory_profiler

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.sec_filings import retrieve_sec_filings
from app.market_data import fetch_market_data
from app.data_enrichment import enrich_filings_data
from utils.logger import get_logger

logger = get_logger('performance_tests')

@pytest.mark.performance
def test_sec_filings_retrieval_performance():
    """
    Performance test for SEC filings retrieval.
    Measures execution time and memory usage.
    """
    # Test multiple CIKs to simulate bulk retrieval
    test_ciks = [
        '0001318605', '0001652044', '0001067983', 
        '0001326801', '0001166559', '0001551152'
    ]

    start_time = time.time()
    
    # Use memory_profiler to track memory usage
    @memory_profiler.profile
    def retrieve_filings():
        all_filings = []
        for cik in test_ciks:
            filings = retrieve_sec_filings(cik=cik, form_type='13G')
            all_filings.extend(filings)
        return all_filings

    filings = retrieve_filings()
    
    end_time = time.time()
    execution_time = end_time - start_time

    # Performance assertions
    assert len(filings) > 0, "No filings retrieved"
    assert execution_time < 10.0, f"Retrieval took too long: {execution_time} seconds"
    
    logger.info(f"SEC Filings Retrieval Performance Test")
    logger.info(f"Number of Filings Retrieved: {len(filings)}")
    logger.info(f"Execution Time: {execution_time:.2f} seconds")

@pytest.mark.performance
def test_market_data_enrichment_performance():
    """
    Performance test for market data enrichment.
    Measures execution time and memory usage for data processing.
    """
    # Prepare test data
    test_filings = [
        {
            'cik': '0001318605',
            'symbol': 'AAPL',
            'shares_owned': 5000000,
            'percent_of_class': 7.5
        },
        {
            'cik': '0001652044',
            'symbol': 'MSFT',
            'shares_owned': 3000000,
            'percent_of_class': 5.2
        }
    ]

    start_time = time.time()
    
    # Use memory_profiler to track memory usage
    @memory_profiler.profile
    def enrich_data():
        enriched_data = []
        for filing in test_filings:
            market_data = fetch_market_data(filing['symbol'])
            enriched_filing = enrich_filings_data([filing], market_data)[0]
            enriched_data.append(enriched_filing)
        return enriched_data

    enriched_filings = enrich_data()
    
    end_time = time.time()
    execution_time = end_time - start_time

    # Performance assertions
    assert len(enriched_filings) == len(test_filings), "Not all filings were enriched"
    assert execution_time < 5.0, f"Enrichment took too long: {execution_time} seconds"
    
    # Validate enriched data
    for filing in enriched_filings:
        assert 'market_cap' in filing, "Market cap not calculated"
        assert 'stock_price' in filing, "Stock price not retrieved"
        assert 'ownership_value' in filing, "Ownership value not calculated"

    logger.info(f"Market Data Enrichment Performance Test")
    logger.info(f"Number of Filings Enriched: {len(enriched_filings)}")
    logger.info(f"Execution Time: {execution_time:.2f} seconds")

@pytest.mark.performance
def test_data_processing_scalability():
    """
    Scalability test to measure performance with increasing data volume.
    """
    def generate_test_filings(count):
        """
        Generate synthetic test filings.
        """
        return [
            {
                'cik': f'000{i}',
                'symbol': f'SYMBOL{i}',
                'shares_owned': 1000000 * (i + 1),
                'percent_of_class': 5.0 + (i * 0.1)
            } for i in range(count)
        ]

    # Test different data volumes
    test_volumes = [10, 100, 1000]
    
    for volume in test_volumes:
        test_filings = generate_test_filings(volume)
        
        start_time = time.time()
        
        @memory_profiler.profile
        def process_filings():
            processed_data = []
            for filing in test_filings:
                market_data = fetch_market_data(filing['symbol'])
                enriched_filing = enrich_filings_data([filing], market_data)[0]
                processed_data.append(enriched_filing)
            return processed_data
        
        processed_filings = process_filings()
        
        end_time = time.time()
        execution_time = end_time - start_time

        logger.info(f"Scalability Test - Volume: {volume} filings")
        logger.info(f"Execution Time: {execution_time:.2f} seconds")
        
        # Scalability assertion (time should grow sub-linearly)
        assert execution_time < (volume * 0.1), f"Processing time too high for {volume} filings"
        assert len(processed_filings) == volume, "Not all filings processed"
