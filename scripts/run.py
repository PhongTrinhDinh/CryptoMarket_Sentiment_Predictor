import sys
from pathlib import Path
import argparse
import logging

FILE = Path(__file__).resolve()
ROOT = FILE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
    
from apps.db.database import init_db
from apps.ingestion.market import fetch_store_ohlcv
from apps.ingestion.news import fetch_crypto_news
from apps.nlp.sentiment import analyze_update_sentiments
from apps.features.builder import build_training_dataset

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MAIN RUNNER")

def run_ingestion():
    logger.info("=== START: DATA INGESTION ===")
    fetch_store_ohlcv(symbol='BTC/USDT', timeframe='15m')
    fetch_crypto_news(query='Bitcoin OR BTC', target_entity="BTC")
    logger.info("=== DONE: DATA INGESTION ===")
    
def run_sentiment():
    logger.info("=== START: NLP SENTIMENT ANALYSIS ===")
    analyze_update_sentiments(limit=500)
    logger.info("=== DONE: NLP SENTIMENT ANALYSYS ===")
    
def run_features():
    logger.info("=== START: FEATURES ENGINEERING ===")
    df = build_training_dataset(symbol='BTC/USDT', entity='BTC', lookahead_candless=4)
    if not df.empty:
        logger.info(f"=== DATASET READY! SHAPE {df.shape}")
    logger.info("=== DONE: FEATURES ENGINEERING ===")
    
def main():
    parser = argparse.ArgumentParser(description="Market Sentiment Predictor Pipeline")
    parser.add_argument(
        '--task',
        type=str,
        choices=['ingest', 'sentiment', 'features', 'all'],
        default='all',
        help='Select the stage to run (default: run all)'
    )
    
    args = parser.parse_args()
    
    init_db()
    
    if args.task == 'ingest':
        run_ingestion()
    elif args.task == 'sentiment':
        run_sentiment()
    elif args.task == 'features':
        run_features()
    elif args.task == 'all':
        run_ingestion()
        run_sentiment()
        run_features()
        
if __name__ == "__main__":
    main()