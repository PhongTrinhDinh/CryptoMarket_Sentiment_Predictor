import sys
from pathlib import Path

FILE = Path(__file__).resolve()
ROOT = FILE.parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import pandas as pd
import pandas_ta as ta
import logging
from sqlalchemy import desc

from apps.db.database import SessionLocal
from apps.db.models import MarketData

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_technical_features(symbol: str = "BTC/USDT", limit: int = 500) -> pd.DataFrame:
    db = SessionLocal()
    try:
        query = db.query(MarketData).filter(MarketData.symbol == symbol).order_by(desc(MarketData.timestamp)).limit(limit)
        
        df = pd.read_sql(query.statement, db.bind)
        
        if df.empty:
            logger.warning(f"No data for {symbol}")
            return df
        
        df = df.sort_values(by='timestamp', ascending=True).reset_index(drop=True)
        df.set_index('timestamp', inplace=True)
        
        logger.info("Calculating indicators: RSI, MACD, Bollinger Bands...")
        df.ta.rsi(length=14, append=True)
        df.ta.macd(fast=12, slow=26, signal=9, append=True)
        df.ta.bbands(length=20, std=2, append=True)
        df.dropna(inplace=True)
        logger.info(f"Calculation complete! The DataFrame is ready with {df.shape[0]} rows and {df.shape[1]} columns.")
        
        return df
    
    except Exception as e:
        logger.error(f"Error calculating technical features: {e}")
        return pd.DataFrame()
    finally:
        db.close()
        
