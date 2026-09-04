# Crypto Market Sentiment Predictor

A data engineering and machine learning pipeline that fetches cryptocurrency market data alongside news articles, performs NLP-based sentiment analysis, engineers features, and serves real-time market sentiment predictions via an interactive dashboard.

## 🚀 Overview
The Market Sentiment Predictor is designed to continuously ingest financial data, process unstructured news into structured sentiment scores using Large Language Models (LLMs), combine these into a unified dataset, train an XGBoost model, and serve predictions in real time.

The pipeline consists of five main stages:
1. **Data Ingestion**: Fetches historical OHLCV data from cryptocurrency exchanges (e.g., Binance) and scrapes relevant financial news.
2. **NLP Sentiment Analysis**: Evaluates the scraped news content to generate a sentiment score and reasoning using Ollama / OpenAI.
3. **Feature Engineering**: Merges technical market indicators and news sentiment scores, generating a clean dataset.
4. **Machine Learning Model**: Trains an XGBoost Classifier with `softprob` to output movement probabilities (Up, Down, Sideways).
5. **Real-time Serving & Dashboard**: A FastAPI backend serves predictions, and a Streamlit dashboard visualizes the data interactively.

## 🛠️ Features
- **Crypto Market Data**: Integration with CCXT to reliably fetch OHLCV data.
- **NLP Sentiment Engine**: Automated scoring of text sentiment and reasoning extraction to gauge market mood.
- **Machine Learning (XGBoost)**: Predicts the market direction of the next candles based on technical and sentiment features.
- **FastAPI Backend**: A highly performant API that loads the model directly into RAM for fast real-time inference.
- **Streamlit Dashboard**: A professional interactive UI providing Hero Action Signals, Model Confidence Breakdown, Technical Candlestick Charts, and a Live Sentiment Feed.
- **Robust Storage**: PostgreSQL with TimescaleDB for highly efficient time-series data storage, alongside Redis for caching.
- **Fully Dockerized**: Easily run the entire stack (DB, Cache, API, Dashboard) with a single command.

## 💻 Tech Stack
- **Language**: Python 3.12+
- **Machine Learning**: XGBoost, Scikit-learn, Pandas, Numpy
- **Web & API**: FastAPI, Uvicorn, Streamlit
- **Data Visualization**: Plotly
- **Database & Caching**: PostgreSQL (TimescaleDB), Redis, SQLAlchemy
- **Infrastructure**: Docker, Docker Compose

## ⚙️ Installation & Usage

### 1. Prerequisites
- Docker and Docker Compose installed.
- A `.env` file in the root directory containing your database credentials and API keys (e.g., NewsAPI).

**Example `.env`**:
```env
POSTGRES_USER=phong
POSTGRES_PASSWORD=your_password
POSTGRES_DB=market_sentiment_db
# POSTGRES_HOST is handled automatically in Docker Compose
NEWSAPI_KEY=your_newsapi_key
```

### 2. Run the Entire Stack (Recommended)
You can spin up the PostgreSQL Database, Redis Cache, FastAPI Backend, and Streamlit Dashboard simultaneously using Docker Compose:

```bash
docker-compose up --build -d
```

Once all containers are running:
- **Interactive Dashboard (Streamlit)**: [http://localhost:8501](http://localhost:8501)
- **API Documentation (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)

To stop the stack:
```bash
docker-compose down
```

### 3. Running Data Pipelines Manually (Optional)
If you wish to run ingestion, sentiment extraction, feature building, or model training manually, you can set up a local virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Run specific pipeline tasks:
```bash
# Data pipelines
python scripts/run.py --task ingest
python scripts/run.py --task sentiment
python scripts/run.py --task features

# Model training
python apps/models/train.py
```

### 4. Running Tests
Execute the test suite to ensure the API and modules are working correctly:
```bash
pytest tests/
```
