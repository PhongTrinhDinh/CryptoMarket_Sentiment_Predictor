# Market Sentiment Predictor

A data engineering and machine learning pipeline that fetches cryptocurrency market data alongside news articles, performs NLP-based sentiment analysis, and engineers features to predict market sentiment and price movements.

## Overview
The Market Sentiment Predictor is designed to continuously ingest financial data, process unstructured news into structured sentiment scores, and combine these into a unified dataset ready for machine learning models. 

The pipeline consists of three main stages:
1. **Data Ingestion**: Fetches historical OHLCV (Open, High, Low, Close, Volume) data from cryptocurrency exchanges and scrapes relevant financial news.
2. **Sentiment Analysis**: Evaluates the scraped news content to generate a sentiment score (bullish, bearish, or neutral).
3. **Feature Engineering**: Merges market data and sentiment scores, generating a clean dataset with engineered features suitable for predictive modeling.

## Features
- **Crypto Market Data**: Integration with CCXT to reliably fetch OHLCV data from Binance and other major exchanges.
- **News Aggregation**: Automated ingestion of cryptocurrency news and articles.
- **NLP Sentiment Engine**: Automated scoring of text sentiment to gauge market mood.
- **Robust Storage**: Uses PostgreSQL combined with TimescaleDB for highly efficient time-series data storage and querying.
- **Automated Pipeline**: A centralized runner script to execute individual stages or the entire pipeline end-to-end.

## Tech Stack
- **Language**: Python 3.12+
- **Database**: PostgreSQL with TimescaleDB extension
- **ORM**: SQLAlchemy
- **Data Processing**: Pandas, CCXT
- **Testing**: pytest, pytest-mock
- **Infrastructure**: Docker, Docker Compose

## Requirements
- Python 3.12 or higher
- Docker and Docker Compose (for running the database easily)
- A `.env` file containing your database credentials and API keys (e.g., NewsAPI, OpenAI).

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/PhongTrinhDinh/CryptoMarket_Sentiment_Predictor.git
   cd CryptoMarket_Sentiment_Predictor
   ```

2. **Set up a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   *(Assuming a `requirements.txt` is present or using pip directly)*
   ```bash
   pip install -r requirements.txt
   ```
   *(Or install the core packages manually: `pip install ccxt pandas sqlalchemy psycopg2-binary pytest pytest-mock python-dotenv`)*

4. **Environment Variables:**
   Create a `.env` file in the root directory and populate it with your credentials:
   ```env
   POSTGRES_USER=your_user
   POSTGRES_PASSWORD=your_password
   POSTGRES_DB=market_sentiment_db
   POSTGRES_HOST=localhost
   ```

## Deployment and Usage

1. **Start the Database:**
   Use Docker Compose to spin up the PostgreSQL/TimescaleDB container.
   ```bash
   docker-compose up -d
   ```

2. **Run the Pipeline:**
   You can run the entire pipeline or specific tasks using the main runner script.
   
   To run the full pipeline (Ingestion -> Sentiment -> Features):
   ```bash
   python scripts/run.py --task all
   ```
   
   To run a specific stage:
   ```bash
   python scripts/run.py --task ingest
   python scripts/run.py --task sentiment
   python scripts/run.py --task features
   ```

3. **Running Tests:**
   Execute the test suite to ensure everything is working correctly.
   ```bash
   python -m pytest tests/
   ```
