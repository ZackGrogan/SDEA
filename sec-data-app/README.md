# SEC Holdings Intelligence Platform (SHIP)

## Project Overview
SHIP is an advanced data analysis platform designed to process and analyze SEC Form 13G and 13D filings. The platform provides comprehensive insights into institutional shareholding, ownership changes, and market dynamics.

## Project Details
- **Name**: SEC Holdings Intelligence Platform
- **Acronym**: SHIP
- **Contact**: zackariahgrogan@gmail.com
- **Purpose**: Academic Research Project for Analyzing Institutional Ownership

## Key Features
- Retrieve and parse SEC EDGAR filings
- Extract detailed shareholder information
- Track ownership threshold changes
- Enrich data with market performance metrics
- Visualize institutional investment trends

## Prerequisites
- Python 3.10.11+
- pip
- Virtual environment support

## Setup Instructions
1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Install spaCy Language Model:
   ```bash
   python -m spacy download en_core_web_sm
   ```

## Running the Application
```bash
python app/main.py
```

## Project Structure
- `app/`: Backend modules
  - `sec_filings.py`: SEC filing retrieval
  - `market_data.py`: Stock market data retrieval
  - `data_enrichment.py`: Data processing and enrichment
- `data/`: Data storage
- `docs/`: Project documentation
- `templates/`: HTML templates

## Data Sources
- SEC EDGAR Full-Text Search API
- yfinance for market data retrieval

## Advanced Features
- Asynchronous data retrieval
- NLP-powered text analysis
- Intelligent caching mechanisms
- Rate-limited API interactions

## Troubleshooting
- If you encounter issues with the spaCy language model, ensure you've run `python -m spacy download en_core_web_sm`
- Verify all dependencies are correctly installed in your virtual environment

## Compliance and Ethics
This project is for academic research purposes. All data retrieval and usage comply with SEC guidelines and fair use policies.
