import requests
import time
import json
from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .logger import sec_filings_logger

class SECAPIClient:
    BASE_URL = "https://www.sec.gov/edgar/search-index"
    COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
    
    def __init__(self, user_agent: str = "SEC Filing Analyzer (contact@example.com)"):
        self.session = self._create_session()
        self.headers = {
            "User-Agent": user_agent,
            "Accept": "application/json",
        }
        self.rate_limit_delay = 0.1  # 100ms between requests
        self.last_request_time = 0
        
    def _create_session(self) -> requests.Session:
        """Create session with retry mechanism"""
        session = requests.Session()
        retry_strategy = Retry(
            total=5,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def _respect_rate_limit(self):
        """Ensure rate limit compliance"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last_request)
        self.last_request_time = time.time()
    
    def get_filings(self, form_types: List[str], start_date: str, end_date: str) -> List[Dict]:
        """
        Retrieve SEC filings with pagination handling
        """
        filings = []
        page = 1
        
        while True:
            self._respect_rate_limit()
            
            params = {
                "formTypes": form_types,
                "startDate": start_date,
                "endDate": end_date,
                "page": page,
            }
            
            response = self.session.get(
                self.BASE_URL,
                headers=self.headers,
                params=params
            )
            
            try:
                response.raise_for_status()
                data = response.json()
                
                # Extract filings
                page_filings = data.get('hits', [])
                filings.extend(page_filings)
                
                # Check if there are more pages
                if len(page_filings) < 100:  # Assuming 100 results per page
                    break
                
                page += 1
                
            except requests.exceptions.RequestException as e:
                sec_filings_logger.error(f"Error retrieving filings: {str(e)}")
                break
        
        return filings
    
    def get_company_tickers(self) -> Dict:
        """
        Retrieve company tickers mapping
        """
        try:
            self._respect_rate_limit()
            response = self.session.get(
                self.COMPANY_TICKERS_URL,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            sec_filings_logger.error(f"Error retrieving company tickers: {str(e)}")
            raise

class FilingRetriever:
    def __init__(self, api_client: SECAPIClient):
        self.api_client = api_client
        self.company_tickers = None
    
    def _load_company_tickers(self):
        """Load and cache company tickers"""
        if self.company_tickers is None:
            self.company_tickers = self.api_client.get_company_tickers()
    
    def retrieve_filings(self, start_year: int, end_year: int) -> pd.DataFrame:
        """
        Retrieve and process SEC filings
        """
        try:
            self._load_company_tickers()
            
            start_date = f"{start_year}-01-01"
            end_date = f"{end_year}-12-31"
            
            form_types = ["13D", "13G", "13D/A", "13G/A"]
            
            filings = self.api_client.get_filings(form_types, start_date, end_date)
            
            # Convert to DataFrame for easier processing
            df = pd.DataFrame(filings)
            
            # Add company information
            df = self._enrich_company_info(df)
            
            return df
            
        except Exception as e:
            sec_filings_logger.error(f"Error in filing retrieval process: {str(e)}")
            raise
    
    def _enrich_company_info(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich filings with company information
        """
        # Add company name and ticker from mapping
        ticker_mapping = {
            cik: {
                'ticker': info['ticker'],
                'name': info['title']
            }
            for cik, info in self.company_tickers.items()
        }
        
        df['ticker'] = df['cik'].map(lambda x: ticker_mapping.get(x, {}).get('ticker'))
        df['company_name'] = df['cik'].map(lambda x: ticker_mapping.get(x, {}).get('name'))
        
        return df
