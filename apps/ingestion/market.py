import ccxt
import logging
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import insert
from apps.db.database import SessionLocal, init_db
from apps.db.models import MarketData

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fetch_store_ohlcv(symbol: str = "BTC/USDT", timeframe: str = '15m', limit: int = 100):
    exchange = ccxt.binance({
        'enableRateLimit': True,
    })
    
    try:
        logger.info(f"Fetching {limit} {timeframe} candles for {symbol} from {exchange.id}...")
        ohlcv_data = exchange.fetch_ohlcv(symbol, timeframe, limit)
        if not ohlcv_data:
            logger.warning("No data returned from the exchange.")
            return
        
        records = []
        for candle in ohlcv_data:
            ts_utc = datetime.fromtimestamp(candle[0] / 1000, tz=timezone.utc)
            records.append({
                "symbol": symbol,
                "timestamp": ts_utc,
                "open": float(candle[1]),
                "high": float(candle[2]),
                "low": float(candle[3]),
                "close": float(candle[4]),
                "volume": float(candle[5])
            })
            
        db = SessionLocal()
        try:
            stmt = insert(MarketData).values(records)
            update_dict = {
                'open': stmt.excluded.open,
                'high': stmt.excluded.high,
                'low': stmt.excluded.low,
                'close': stmt.excluded.close,
                'volume': stmt.excluded.volume
            }
            stmt = stmt.on_conflict_do_update(
                index_elements=['symbol', 'timestamp'],
                set_=update_dict
            )
            
            db.execute(stmt)
            db.commit()
            
            logger.info(f"Successfully saved {len(records)} records to the database.")
            
        except Exception as db_error:
            db.rollback()
            logger.error(f"Error saving to database: {db_error}")
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error fetching data from CCXT: {e}")
        
if __name__ == "__main__":
    logger.info("Checking and initializing the database...")
    init_db()
    fetch_store_ohlcv(symbol='BTC/USDT', timeframe='15m', limit=1000)