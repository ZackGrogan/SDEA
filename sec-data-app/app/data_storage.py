import sqlite3
import pandas as pd
from typing import Optional, List, Dict
from datetime import datetime
import json
import os
from .logger import data_parsing_logger as storage_logger

class DataStorage:
    def __init__(self, db_path: str = 'sec_filings.db'):
        self.db_path = db_path
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize database with optimized schema"""
        try:
            # Ensure data directory exists
            os.makedirs('data', exist_ok=True)
            
            # Connect to SQLite database
            with sqlite3.connect(os.path.join('data', self.db_path)) as conn:
                cursor = conn.cursor()
                
                # Create filings table with indexes
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS filings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cik TEXT NOT NULL,
                        cusip TEXT,
                        ticker TEXT,
                        company_name TEXT,
                        filing_type TEXT NOT NULL,
                        filing_date DATE NOT NULL,
                        ownership_percentage REAL,
                        market_cap REAL,
                        performance_data TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for frequent queries
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_cik ON filings(cik)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_cusip ON filings(cusip)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_ticker ON filings(ticker)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_filing_date ON filings(filing_date)")
                
                # Create threshold exits table with indexes
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS threshold_exits (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        filing_id INTEGER,
                        cik TEXT NOT NULL,
                        cusip TEXT,
                        ticker TEXT,
                        company_name TEXT,
                        exit_date DATE NOT NULL,
                        previous_percentage REAL,
                        current_percentage REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (filing_id) REFERENCES filings(id)
                    )
                """)
                
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_exit_date ON threshold_exits(exit_date)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_filing_id ON threshold_exits(filing_id)")
                
                conn.commit()
                
            storage_logger.info(f"Storage initialized at {self.db_path}")
        
        except Exception as e:
            storage_logger.error(f"Database initialization error: {str(e)}")
            raise
    
    def store_data(self, df: pd.DataFrame):
        """Store data with batch processing"""
        try:
            with sqlite3.connect(os.path.join('data', self.db_path)) as conn:
                # Find performance columns dynamically
                performance_cols = [col for col in df.columns if col.startswith('performance_') or 'performance' in col.lower()]
                
                # If performance columns exist, convert to JSON
                if performance_cols:
                    df['performance_data'] = df[performance_cols].to_dict('records')
                else:
                    df['performance_data'] = [{}] * len(df)
                
                # Prepare data for filings table
                filings_data = df[[
                    'cik', 'cusip', 'ticker', 'company_name', 'form_type',
                    'filing_date', 'ownership_percentage', 'market_cap', 'performance_data'
                ]].copy()
                
                # Convert performance data to JSON string
                filings_data['performance_data'] = filings_data['performance_data'].apply(json.dumps)
                
                # Store in batches
                batch_size = 1000
                for i in range(0, len(filings_data), batch_size):
                    batch = filings_data.iloc[i:i + batch_size]
                    batch.to_sql('filings', conn, if_exists='append', index=False)
                
                conn.commit()
                
            storage_logger.info(f"Stored {len(df)} filings")
        
        except Exception as e:
            storage_logger.error(f"Data storage error: {str(e)}")
            raise
    
    def store_threshold_exits(self, exits_df: pd.DataFrame):
        """Store threshold exits with batch processing"""
        try:
            with sqlite3.connect(os.path.join('data', self.db_path)) as conn:
                # Prepare data for threshold_exits table
                exits_data = exits_df[[
                    'filing_id', 'cik', 'cusip', 'ticker', 'company_name',
                    'exit_date', 'previous_percentage', 'current_percentage'
                ]].copy()
                
                # Store in batches
                batch_size = 1000
                for i in range(0, len(exits_data), batch_size):
                    batch = exits_data.iloc[i:i + batch_size]
                    batch.to_sql('threshold_exits', conn, if_exists='append', index=False)
                
                conn.commit()
                
            storage_logger.info(f"Stored {len(exits_df)} threshold exits")
        
        except Exception as e:
            storage_logger.error(f"Threshold exits storage error: {str(e)}")
            raise
    
    def retrieve_data(self, table: str, conditions: Optional[Dict] = None) -> pd.DataFrame:
        """Retrieve data with optimized query"""
        try:
            with sqlite3.connect(os.path.join('data', self.db_path)) as conn:
                query = f"SELECT * FROM {table}"
                
                if conditions:
                    where_clauses = []
                    params = []
                    for key, value in conditions.items():
                        where_clauses.append(f"{key} = ?")
                        params.append(value)
                    
                    if where_clauses:
                        query += " WHERE " + " AND ".join(where_clauses)
                
                # Use pandas read_sql for efficient data loading
                df = pd.read_sql(query, conn, params=params if conditions else None)
                
                # Parse performance data if present
                if 'performance_data' in df.columns:
                    df['performance_data'] = df['performance_data'].apply(
                        lambda x: json.loads(x) if x else {}
                    )
                
                storage_logger.info(f"Retrieved {len(df)} filings")
                return df
                
        except Exception as e:
            storage_logger.error(f"Data retrieval error: {str(e)}")
            raise
    
    def save_filings(self, filings):
        """
        Save filings to the database, handling various input formats.
        
        Args:
            filings (list or pd.DataFrame): Filings to save
        """
        try:
            # Convert list of dictionaries to DataFrame if needed
            if isinstance(filings, list):
                df = pd.DataFrame(filings)
            elif isinstance(filings, pd.DataFrame):
                df = filings.copy()
            else:
                raise ValueError("Filings must be a list of dictionaries or a DataFrame")
            
            # Standardize column names
            column_mapping = {
                'percent_of_class': 'ownership_percentage',
                'stock_price': 'market_price'
            }
            df.rename(columns=column_mapping, inplace=True)
            
            # Add missing columns with default values if not present
            required_columns = [
                'cik', 'form_type', 'filing_date', 
                'ownership_percentage', 'market_cap'
            ]
            optional_columns = [
                'cusip', 'ticker', 'company_name', 
                'performance_data'
            ]
            
            # Fill missing required columns
            for col in required_columns:
                if col not in df.columns:
                    df[col] = None
            
            # Fill optional columns
            for col in optional_columns:
                if col not in df.columns:
                    df[col] = None
            
            # Ensure performance_data is a list of dictionaries
            if 'performance_data' not in df.columns or df['performance_data'].isnull().all():
                df['performance_data'] = [{}] * len(df)
            
            # Store the data
            self.store_data(df)
            
        except Exception as e:
            storage_logger.error(f"Error saving filings: {str(e)}")
            raise
    
    def load_filings(self, conditions: Optional[Dict] = None) -> List[Dict]:
        """
        Load filings from the database.
        
        :param conditions: Optional dictionary of conditions to filter filings
        :return: List of filing dictionaries
        """
        df = self.retrieve_data('filings', conditions)
        return df.to_dict('records')
