import sys
from pathlib import Path

FILE = Path(__file__).resolve()
ROOT = FILE.parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
    
import pandas as pd
import numpy as np
import logging
from apps.db.database import SessionLocal
from apps.db.models import NewsSentiment
from apps.features.technical import get_technical_features

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_aggregated_sentiment(entity: str = 'BTC', limit: int = 5000) -> pd.DataFrame:
    db = SessionLocal()
    try:
        query = db.query(NewsSentiment.published_at, NewsSentiment.sentiment_score).filter(NewsSentiment.entity == entity).order_by(NewsSentiment.published_at.desc()).limit(limit)
        
        df_news = pd.read_sql(query.statement, db.bind)
        
        if df_news.empty:
            logger.warning(f"No sentiment data for {entity}")
            return pd.DataFrame()
        
        df_news.rename(columns={'published_at': 'timestamp'}, inplace=True)
        df_news.set_index('timestamp', inplace=True)
        
        sentiment_15m = df_news.resample('15min', closed='left', label='left').mean()
        
        return sentiment_15m
    
    except Exception as e:
        logger.error(f"Error processing sentiment data: {e}")
        return pd.DataFrame()
    
    finally:
        db.close()
        
def build_training_dataset(symbol: str = 'BTC/USDT', entity: str = 'BTC', lookahead_candless: int = 4) -> pd.DataFrame:
    logger.info("Preparing Technical Features...")
    df_tech = get_technical_features(symbol, limit=2000)
    
    if df_tech.empty:
        return df_tech
    
    logger.info("Aggregating sentiment score...")
    df_sentiment = get_aggregated_sentiment(entity)
    
    logger.info("Merging data (Join)...")
    if not df_sentiment.empty:
        df_merged = df_tech.join(df_sentiment, how='left')
        df_merged['sentiment_score'] = df_merged['sentiment_score'].fillna(0.0)
    else:
        df_merged = df_tech.copy()
        df_merged['sentiment_score'] = 0.0
        
    logger.info("Labeling the next {lookahead_candles} candles...")
    df_merged['future_close'] = df_merged['close'].shift(-lookahead_candless)
    df_merged['future_return'] = (df_merged['future_close'] - df_merged['close']) / df_merged['close']
    threshold = 0.005 # 0.5%, Increase if greater than 0.5% (1), decrease if less than -0.5% (-1), Sideways movement (0)
    
    def categorize_return(ret):
        if pd.isna(ret):
            return np.nan # Current candlestick data lacks future data for viewing and will be discarded.
        if ret > threshold:
            return 1
        elif ret < -threshold:
            return -1
        else:
            return 0
        
    df_merged['target_label'] = df_merged['future_return'].apply(categorize_return)
    df_merged.dropna(subset=['target_label'], inplace=True)
    df_merged['target_label'] = df_merged['target_label'].astype(int)
    cols_to_drop = ['future_close', 'future_return']
    if 'id' in df_merged.columns: cols_to_drop.append('id')
    if 'symbol' in df_merged.columns: cols_to_drop.append('symbol')
    df_final = df_merged.drop(columns=cols_to_drop)
    
    logger.info(f"Dataset completed! Size: {df_final.shape}")
    logger.info(f"Class distribution:\n{df_final['target_label'].value_counts()}")
    
    return df_final

