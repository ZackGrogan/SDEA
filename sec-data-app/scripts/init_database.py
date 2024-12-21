import os
import sqlite3
import json

def init_database(db_path):
    """
    Initialize SQLite database with schema for SEC filings.
    
    :param db_path: Path to the SQLite database file
    """
    # Ensure data directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create filings table with comprehensive schema
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS filings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cik TEXT NOT NULL,
        cusip TEXT,
        ticker TEXT,
        company_name TEXT,
        form_type TEXT NOT NULL,
        filing_date TEXT NOT NULL,
        shares_owned INTEGER,
        ownership_percentage REAL,
        market_cap REAL,
        performance_data TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create index for faster querying
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_cik_form_date 
    ON filings (cik, form_type, filing_date)
    ''')
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print(f"Database initialized at {db_path}")

def main():
    # Default database path
    default_db_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'data', 
        'sec_filings.db'
    )
    
    init_database(default_db_path)

if __name__ == '__main__':
    main()
