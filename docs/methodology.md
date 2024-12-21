# Methodology

## Data Collection
- SEC filings retrieved using SEC EDGAR Full-Text Search API.
- Market data obtained through internal financial data APIs.

## Data Parsing
- Filings parsed using BeautifulSoup and lxml.

## Data Enrichment
- Enhanced with stock prices and market capitalization.

## Threshold Tracking
- Identified shareholders below 5% ownership.

## Assumptions
- Consistent data formats assumed across filings.

## Challenges
- Variations in filing formats.

## Solutions
- Robust error handling implemented.
