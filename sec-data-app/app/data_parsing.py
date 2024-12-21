# Data Parsing Module for SEC Filings

from bs4 import BeautifulSoup
import lxml
import re
import pandas as pd
from typing import Dict, List, Any, Optional
from .logger import data_parsing_logger

class SECFilingParser:
    @staticmethod
    def parse_13g_13d(filing_text: str) -> Dict[str, Any]:
        """
        Parse 13G and 13D filings with robust error handling
        
        :param filing_text: Raw text of the filing
        :return: Extracted filing information
        """
        try:
            soup = BeautifulSoup(filing_text, 'lxml')
            
            # Extraction patterns (to be refined)
            extraction_patterns = {
                'beneficial_owner': r'Name of Reporting Person\s*(.+)',
                'shares_owned': r'Total Amount of Shares Beneficially Owned\s*(\d+)',
                'ownership_percentage': r'Percent of Class Represented by Amount in Row\s*(\d+\.\d+)%'
            }
            
            parsed_data = {}
            for key, pattern in extraction_patterns.items():
                match = re.search(pattern, filing_text, re.IGNORECASE)
                if match:
                    parsed_data[key] = match.group(1).strip()
            
            data_parsing_logger.info(f'Successfully parsed filing: {parsed_data}')
            return parsed_data
        
        except Exception as e:
            data_parsing_logger.error(f'Error parsing filing: {e}')
            return {}

class FilingBatchProcessor:
    def __init__(self, parser_cls=SECFilingParser):
        self.parser = parser_cls()
        self.parsed_filings = []
    
    def process_filings(self, filings: List[str]) -> pd.DataFrame:
        """
        Process multiple filings and convert to DataFrame
        
        :param filings: List of filing texts
        :return: DataFrame of parsed filings
        """
        for filing in filings:
            parsed_filing = self.parser.parse_13g_13d(filing)
            self.parsed_filings.append(parsed_filing)
        
        return pd.DataFrame(self.parsed_filings)

def parse_filing_content(filing_text: str) -> Optional[Dict[str, Any]]:
    """
    Main entry point for parsing a single SEC filing
    
    :param filing_text: Raw text of the filing
    :return: Parsed filing data or None if parsing fails
    """
    try:
        parser = SECFilingParser()
        parsed_data = parser.parse_13g_13d(filing_text)
        
        if not parsed_data:
            data_parsing_logger.warning('Failed to parse filing content')
            return None
        
        return parsed_data
    
    except Exception as e:
        data_parsing_logger.error(f'Unexpected error in parse_filing_content: {e}')
        return None

def parse_sec_filings(filings: List[str]) -> pd.DataFrame:
    """
    Process multiple SEC filings
    
    :param filings: List of filing texts
    :return: Processed DataFrame of filings
    """
    processor = FilingBatchProcessor()
    return processor.process_filings(filings)
