# Market Data Retrieval Module

import asyncio
import aiohttp
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta

from .logger import market_data_logger
from .rate_limiter import RateLimiter
from .cache_manager import CacheManager

def adjust_for_splits_and_dividends(historical_data: pd.DataFrame) -> pd.DataFrame:
    """
    Adjust historical price data for stock splits and dividends.
    
    :param historical_data: Historical stock price DataFrame
    :return: Adjusted historical data
    """
    try:
        # Placeholder for more complex split/dividend adjustment
        # This is a simplified version and might need more sophisticated logic
        historical_data['Adjusted Close'] = historical_data['Close']
        return historical_data
    except Exception as e:
        market_data_logger.warning(f'Could not adjust for splits/dividends: {e}')
        return historical_data

def calculate_performance_metrics(
    historical_data: pd.DataFrame, 
    reference_date: Optional[str] = None
) -> Dict[str, float]:
    """
    Calculate stock performance metrics around a reference date.
    
    :param historical_data: Historical stock price data
    :param reference_date: Date to calculate performance from (defaults to latest date)
    :return: Dictionary of performance metrics
    """
    try:
        # Use the last date if no reference date is provided
        if reference_date is None:
            reference_date = historical_data.index[-1]
        
        reference_date = pd.to_datetime(reference_date)
        
        # Ensure the reference date exists in the index
        if reference_date not in historical_data.index:
            market_data_logger.warning(f'Reference date {reference_date} not found in historical data')
            return {}
        
        current_price = historical_data.loc[reference_date, 'Close']
        performance_metrics = {'current_price': current_price}
        
        # Performance intervals in days
        intervals = [7, 30, 182, 365, 730]
        
        for interval in intervals:
            try:
                past_date = reference_date - pd.Timedelta(days=interval)
                
                # Find the closest available date if exact date is not in index
                if past_date not in historical_data.index:
                    past_date = historical_data.index[historical_data.index <= past_date][-1]
                
                past_price = historical_data.loc[past_date, 'Close']
                performance = ((current_price - past_price) / past_price) * 100
                performance_metrics[f'performance_{interval}d'] = round(performance, 2)
            except Exception as e:
                market_data_logger.warning(f'Performance calculation error for {interval} days: {e}')
        
        return performance_metrics
    
    except Exception as e:
        market_data_logger.error(f'Performance metrics calculation error: {e}')
        return {}

class MarketDataRetriever:
    def __init__(
        self, 
        rate_limit: int = 5,  # Respect yfinance rate limits
        cache_ttl: int = 3600  # 1-hour cache
    ):
        """
        Enhanced market data retrieval with rate limiting and caching.
        
        :param rate_limit: Maximum requests per second
        :param cache_ttl: Cache time-to-live in seconds
        """
        self.rate_limiter = RateLimiter(max_requests=rate_limit)
        self.cache_manager = CacheManager()
        self.cache_ttl = cache_ttl

    async def retrieve_market_data(
        self, 
        symbols: List[str], 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Asynchronously retrieve comprehensive market data for given stock symbols.
        
        :param symbols: List of stock symbols
        :param start_date: Start date for historical data retrieval
        :param end_date: End date for historical data retrieval
        :return: Dictionary of market data
        """
        # Validate and set default dates
        end_date = end_date or datetime.now().strftime('%Y-%m-%d')
        start_date = start_date or (datetime.now() - timedelta(days=5*365)).strftime('%Y-%m-%d')

        tasks = [self._fetch_symbol_data(symbol, start_date, end_date) for symbol in symbols]
        market_data = await asyncio.gather(*tasks)
        
        # Convert list of market data to dictionary
        return {symbol: data for symbol, data in zip(symbols, market_data)}

    async def _fetch_symbol_data(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str
    ) -> Dict[str, Any]:
        """
        Fetch comprehensive market data for a single symbol.
        
        :param symbol: Stock symbol
        :param start_date: Start date for historical data
        :param end_date: End date for historical data
        :return: Dictionary of market data
        """
        async with self.rate_limiter:
            try:
                # Check cache first
                cache_key = f'market_data_{symbol}_{start_date}_{end_date}'
                cached_data = self.cache_manager.get(cache_key)
                if cached_data:
                    return cached_data
                
                # Fetch stock data
                stock = yf.Ticker(symbol)
                
                # Retrieve historical data
                historical_data = stock.history(start=start_date, end=end_date)
                historical_data = adjust_for_splits_and_dividends(historical_data)
                
                # Calculate performance metrics
                performance_metrics = calculate_performance_metrics(historical_data)
                
                # Compile comprehensive market data
                market_data = {
                    'symbol': symbol,
                    'company_name': stock.info.get('longName', 'N/A'),
                    'current_price': stock.info.get('currentPrice', None),
                    'market_cap': stock.info.get('marketCap', None),
                    'sector': stock.info.get('sector', 'N/A'),
                    'historical_data': historical_data.to_dict(),
                    'performance_metrics': performance_metrics
                }
                
                # Cache the result
                self.cache_manager.set(
                    cache_key, 
                    market_data, 
                    expire_seconds=self.cache_ttl
                )
                
                return market_data
            
            except Exception as e:
                market_data_logger.error(f'Error retrieving market data for {symbol}: {e}')
                return {}

async def main():
    """
    Example usage of market data retrieval
    """
    retriever = MarketDataRetriever()
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    market_data = await retriever.retrieve_market_data(symbols)
    print(market_data)

def retrieve_market_data(
    symbols: List[str], 
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Synchronous wrapper for market data retrieval
    
    :param symbols: List of stock symbols
    :param start_date: Start date for historical data retrieval
    :param end_date: End date for historical data retrieval
    :return: Dictionary of market data
    """
    retriever = MarketDataRetriever()
    return asyncio.run(retriever.retrieve_market_data(symbols, start_date, end_date))

if __name__ == '__main__':
    asyncio.run(main())
