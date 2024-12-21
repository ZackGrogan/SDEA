import pytest
import os
import json
from typing import Dict, Any

from app.sec_filings import SECFilingProcessor
from tests.test_utils import mock_sec_filing, validate_test_data

class TestSECFilingProcessor:
    @pytest.fixture
    def sec_filing_processor(self):
        """
        Fixture to create a SECFilingProcessor instance for testing.
        
        Returns:
            SECFilingProcessor: Configured processor instance
        """
        return SECFilingProcessor()

    def test_filing_processor_initialization(self, sec_filing_processor):
        """
        Test initialization of SECFilingProcessor.
        
        Args:
            sec_filing_processor (SECFilingProcessor): Processor instance
        """
        assert sec_filing_processor is not None, "SECFilingProcessor should be initialized"

    def test_parse_filing(self, sec_filing_processor, mock_sec_filing):
        """
        Test parsing of a mock SEC filing.
        
        Args:
            sec_filing_processor (SECFilingProcessor): Processor instance
            mock_sec_filing (Dict[str, Any]): Mock filing data
        """
        parsed_filing = sec_filing_processor.parse_filing(mock_sec_filing)
        
        assert validate_test_data(
            parsed_filing, 
            dict, 
            required_keys=['cik', 'company_name', 'filing_type']
        ), "Parsed filing should be a valid dictionary with required keys"

    def test_validate_filing_data(self, sec_filing_processor, mock_sec_filing):
        """
        Test validation of filing data.
        
        Args:
            sec_filing_processor (SECFilingProcessor): Processor instance
            mock_sec_filing (Dict[str, Any]): Mock filing data
        """
        is_valid = sec_filing_processor.validate_filing_data(mock_sec_filing)
        assert is_valid, "Mock filing data should be considered valid"

    def test_extract_ownership_details(self, sec_filing_processor, mock_sec_filing):
        """
        Test extraction of ownership details from a filing.
        
        Args:
            sec_filing_processor (SECFilingProcessor): Processor instance
            mock_sec_filing (Dict[str, Any]): Mock filing data
        """
        ownership_details = sec_filing_processor.extract_ownership_details(mock_sec_filing)
        
        assert validate_test_data(
            ownership_details, 
            dict, 
            required_keys=['ownership_percentage', 'shares_outstanding']
        ), "Ownership details should be a valid dictionary"

    @pytest.mark.parametrize("invalid_filing", [
        {},  # Empty dictionary
        {'cik': None},  # Missing required fields
        {'company_name': 'Test Corp'}  # Incomplete data
    ])
    def test_invalid_filing_data(self, sec_filing_processor, invalid_filing):
        """
        Test handling of invalid filing data.
        
        Args:
            sec_filing_processor (SECFilingProcessor): Processor instance
            invalid_filing (Dict[str, Any]): Invalid filing data
        """
        with pytest.raises(ValueError, match="Invalid filing data"):
            sec_filing_processor.validate_filing_data(invalid_filing)

    def test_filing_export(self, sec_filing_processor, mock_sec_filing, tmp_path):
        """
        Test exporting filing data to a file.
        
        Args:
            sec_filing_processor (SECFilingProcessor): Processor instance
            mock_sec_filing (Dict[str, Any]): Mock filing data
            tmp_path (Path): Temporary directory path provided by pytest
        """
        export_path = tmp_path / "test_filing_export.json"
        sec_filing_processor.export_filing_data(mock_sec_filing, export_path)
        
        assert os.path.exists(export_path), "Export file should be created"
        
        with open(export_path, 'r') as f:
            exported_data = json.load(f)
        
        assert exported_data == mock_sec_filing, "Exported data should match original filing"
