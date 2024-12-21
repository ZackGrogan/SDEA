import pandas as pd
import numpy as np
import yfinance as yf
import spacy
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import asyncio
import aiohttp

from .logger import enrichment_logger
from .rate_limiter import RateLimiter
from .cache_manager import CacheManager

class DataEnricher:
    def __init__(
        self, 
        rate_limit: int = 5, 
        cache_ttl: int = 3600,
        nlp_model: str = 'en_core_web_sm'
    ):
        """
        Advanced data enrichment with NLP, rate limiting, and caching.
        
        :param rate_limit: Maximum requests per second
        :param cache_ttl: Cache time-to-live in seconds
        :param nlp_model: Spacy NLP model to use
        """
        self.rate_limiter = RateLimiter(max_requests=rate_limit)
        self.cache_manager = CacheManager()
        self.cache_ttl = cache_ttl
        
        # Load NLP model for advanced text analysis
        try:
            self.nlp = spacy.load(nlp_model)
        except OSError:
            enrichment_logger.warning(f"Could not load NLP model {nlp_model}. Text analysis will be limited.")
            self.nlp = None
        
        self.performance_intervals = [7, 30, 182, 365, 730]

    async def enrich_filing_data(self, filings: List[Dict]) -> List[Dict]:
        """
        Asynchronously enrich SEC filing data with market and financial information.
        
        :param filings: List of SEC filing dictionaries
        :return: Enriched filing data
        """
        tasks = [self._enrich_single_filing(filing) for filing in filings]
        enriched_filings = await asyncio.gather(*tasks)
        
        return [filing for filing in enriched_filings if filing]

    async def _enrich_single_filing(self, filing: Dict) -> Optional[Dict]:
        """
        Enrich a single filing with market data and NLP analysis.
        
        :param filing: SEC filing dictionary
        :return: Enriched filing or None
        """
        try:
            # Extract key identifiers
            beneficial_owner = filing.get('beneficial_owner', '')
            shares_owned = filing.get('shares_owned', 0)
            
            # Perform market data enrichment
            market_data = await self._fetch_market_data(beneficial_owner)
            
            # Perform NLP text analysis if possible
            nlp_insights = self._perform_nlp_analysis(beneficial_owner) if self.nlp else {}
            
            # Combine all enrichment data
            enriched_filing = {
                **filing,
                **market_data,
                **nlp_insights,
                'enrichment_timestamp': datetime.utcnow().isoformat()
            }
            
            enrichment_logger.info(f"Enriched filing for {beneficial_owner}")
            return enriched_filing
        
        except Exception as e:
            enrichment_logger.error(f"Enrichment error for filing: {e}")
            return None

    async def _fetch_market_data(self, identifier: str) -> Dict[str, Any]:
        """
        Fetch market data for a given identifier.
        
        :param identifier: Stock symbol or company name
        :return: Market data dictionary
        """
        async with self.rate_limiter:
            try:
                # Check cache first
                cached_data = self.cache_manager.get(f'market:{identifier}')
                if cached_data:
                    return cached_data
                
                # Fetch market data
                ticker = await self._resolve_ticker(identifier)
                if not ticker:
                    return {}
                
                stock = yf.Ticker(ticker)
                
                # Fetch historical data and calculate performance
                market_data = {
                    'ticker': ticker,
                    'current_price': stock.info.get('currentPrice', None),
                    'market_cap': stock.info.get('marketCap', None),
                    'performance': await self._calculate_performance(stock)
                }
                
                # Cache market data
                self.cache_manager.set(
                    f'market:{identifier}', 
                    market_data, 
                    expire_seconds=self.cache_ttl
                )
                
                return market_data
            
            except Exception as e:
                enrichment_logger.error(f"Market data fetch error for {identifier}: {e}")
                return {}

    async def _resolve_ticker(self, identifier: str) -> Optional[str]:
        """
        Resolve a ticker symbol from a company name or identifier.
        
        :param identifier: Company name or other identifier
        :return: Ticker symbol or None
        """
        # Placeholder implementation - in a real-world scenario, 
        # you'd use a more sophisticated mapping or API
        ticker_map = {
            'Apple': 'AAPL',
            'Microsoft': 'MSFT',
            # Add more mappings as needed
        }
        
        return ticker_map.get(identifier, None)

    async def _calculate_performance(self, stock: yf.Ticker) -> Dict[str, float]:
        """
        Calculate stock performance over predefined intervals.
        
        :param stock: yfinance Ticker object
        :return: Performance metrics
        """
        performance = {}
        
        for interval in self.performance_intervals:
            try:
                historical_data = stock.history(period=f'{interval}d')
                if not historical_data.empty:
                    start_price = historical_data['Close'].iloc[0]
                    end_price = historical_data['Close'].iloc[-1]
                    
                    performance_pct = ((end_price - start_price) / start_price) * 100
                    performance[f'performance_{interval}d'] = round(performance_pct, 2)
            except Exception as e:
                enrichment_logger.warning(f"Performance calculation error for {interval}d: {e}")
        
        return performance

    def _perform_nlp_analysis(self, text: str) -> Dict[str, Any]:
        """
        Perform NLP analysis on text using spaCy.
        
        :param text: Text to analyze
        :return: NLP insights
        """
        if not self.nlp:
            return {}
        
        try:
            doc = self.nlp(text)
            
            # Extract named entities
            entities = [
                {
                    'text': ent.text, 
                    'label': ent.label_
                } for ent in doc.ents
            ]
            
            # Basic sentiment (very simplistic)
            sentiment_score = sum(token.sentiment for token in doc if token.has_vector)
            
            return {
                'nlp_entities': entities,
                'nlp_sentiment_score': round(sentiment_score, 2) if sentiment_score else None
            }
        
        except Exception as e:
            enrichment_logger.error(f"NLP analysis error: {e}")
            return {}

def enrich_sec_filings(filings: Union[List[Dict], pd.DataFrame]) -> List[Dict]:
    """
    Main function to enrich SEC filings with market and financial data.
    
    :param filings: List of SEC filings or DataFrame
    :return: List of enriched filings
    """
    # Convert DataFrame to list of dictionaries if needed
    if isinstance(filings, pd.DataFrame):
        filings = filings.to_dict('records')
    
    # Initialize enricher
    enricher = DataEnricher()
    
    # Run enrichment synchronously
    enriched_filings = asyncio.run(enricher.enrich_filing_data(filings))
    
    enrichment_logger.info(f"Enriched {len(enriched_filings)} filings")
    return enriched_filings

async def main():
    """
    Example usage of data enrichment
    """
    # Example filings data
    sample_filings = [
        {'beneficial_owner': 'Apple', 'shares_owned': 1000000},
        {'beneficial_owner': 'Microsoft', 'shares_owned': 500000}
    ]
    
    enricher = DataEnricher()
    enriched_filings = await enricher.enrich_filing_data(sample_filings)
    print(enriched_filings)

if __name__ == '__main__':
    asyncio.run(main())
