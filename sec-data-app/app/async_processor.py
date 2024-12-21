import asyncio
import aiohttp
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from .logger import async_logger
from .sec_api import SECAPIClient
from .market_data import MarketDataClient
from .data_storage import DataStorage

class AsyncProcessor:
    def __init__(self, sec_client: SECAPIClient, market_client: MarketDataClient, storage: DataStorage):
        self.sec_client = sec_client
        self.market_client = market_client
        self.storage = storage
        self.max_workers = 4
        self.semaphore = asyncio.Semaphore(10)  # Limit concurrent requests
    
    async def process_filings_async(self, start_year: int, end_year: int) -> Dict:
        """
        Asynchronously process SEC filings and market data
        """
        try:
            # Create async session
            async with aiohttp.ClientSession() as session:
                # Get filings data
                filings_task = asyncio.create_task(
                    self._get_filings_async(session, start_year, end_year)
                )
                
                # Get company tickers
                tickers_task = asyncio.create_task(
                    self._get_company_tickers_async(session)
                )
                
                # Wait for both tasks
                filings, tickers = await asyncio.gather(filings_task, tickers_task)
                
                # Process filings with tickers
                processed_filings = await self._process_filings(filings, tickers)
                
                # Get market data
                enriched_data = await self._enrich_market_data(processed_filings)
                
                # Store results
                await self._store_results_async(enriched_data)
                
                return {
                    'status': 'success',
                    'filings_count': len(processed_filings),
                    'enriched_count': len(enriched_data)
                }
                
        except Exception as e:
            async_logger.error(f"Async processing error: {str(e)}")
            raise
    
    async def _get_filings_async(self, session: aiohttp.ClientSession, 
                                start_year: int, end_year: int) -> List[Dict]:
        """
        Asynchronously retrieve SEC filings
        """
        async with self.semaphore:
            try:
                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
                    filings = await loop.run_in_executor(
                        pool,
                        partial(
                            self.sec_client.get_filings,
                            ["13D", "13G", "13D/A", "13G/A"],
                            f"{start_year}-01-01",
                            f"{end_year}-12-31"
                        )
                    )
                return filings
            except Exception as e:
                async_logger.error(f"Error retrieving filings: {str(e)}")
                raise
    
    async def _get_company_tickers_async(self, session: aiohttp.ClientSession) -> Dict:
        """
        Asynchronously retrieve company tickers
        """
        async with self.semaphore:
            try:
                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor(max_workers=1) as pool:
                    tickers = await loop.run_in_executor(
                        pool,
                        self.sec_client.get_company_tickers
                    )
                return tickers
            except Exception as e:
                async_logger.error(f"Error retrieving tickers: {str(e)}")
                raise
    
    async def _process_filings(self, filings: List[Dict], tickers: Dict) -> pd.DataFrame:
        """
        Process filings with company information
        """
        try:
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
                df = await loop.run_in_executor(
                    pool,
                    partial(pd.DataFrame, filings)
                )
                
                # Add company information
                ticker_mapping = {
                    cik: {'ticker': info['ticker'], 'name': info['title']}
                    for cik, info in tickers.items()
                }
                
                df['ticker'] = df['cik'].map(lambda x: ticker_mapping.get(x, {}).get('ticker'))
                df['company_name'] = df['cik'].map(lambda x: ticker_mapping.get(x, {}).get('name'))
                
                return df
                
        except Exception as e:
            async_logger.error(f"Error processing filings: {str(e)}")
            raise
    
    async def _enrich_market_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Asynchronously enrich filings with market data
        """
        try:
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
                # Get unique tickers
                tickers = df['ticker'].unique().tolist()
                
                # Get market data for each ticker
                tasks = []
                for ticker in tickers:
                    if ticker:
                        task = loop.run_in_executor(
                            pool,
                            partial(
                                self.market_client.get_stock_data,
                                ticker,
                                df['filing_date'].min(),
                                df['filing_date'].max()
                            )
                        )
                        tasks.append(task)
                
                market_data = await asyncio.gather(*tasks)
                
                # Process market data
                market_dict = dict(zip(tickers, market_data))
                
                # Add market data to DataFrame
                df['market_cap'] = df['ticker'].map(
                    lambda x: self.market_client.get_market_cap(x) if x else None
                )
                
                # Calculate performance metrics
                performance_periods = [7, 30, 182, 365, 730]
                for period in performance_periods:
                    df[f'performance_{period}d'] = df.apply(
                        lambda row: self._calculate_performance(
                            market_dict.get(row['ticker']),
                            row['filing_date'],
                            period
                        ) if row['ticker'] else None,
                        axis=1
                    )
                
                return df
                
        except Exception as e:
            async_logger.error(f"Error enriching market data: {str(e)}")
            raise
    
    def _calculate_performance(self, hist_data: Optional[pd.DataFrame],
                             filing_date: str, days: int) -> Optional[float]:
        """
        Calculate performance metrics
        """
        try:
            if hist_data is None or hist_data.empty:
                return None
            
            filing_date = pd.to_datetime(filing_date)
            start_price = hist_data.loc[filing_date:]['Close'].iloc[0]
            end_date = filing_date + pd.Timedelta(days=days)
            end_price = hist_data.loc[:end_date]['Close'].iloc[-1]
            
            return ((end_price - start_price) / start_price) * 100
            
        except Exception:
            return None
    
    async def _store_results_async(self, df: pd.DataFrame):
        """
        Asynchronously store processed results
        """
        try:
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=1) as pool:
                await loop.run_in_executor(
                    pool,
                    partial(self.storage.store_data, df)
                )
        except Exception as e:
            async_logger.error(f"Error storing results: {str(e)}")
            raise
