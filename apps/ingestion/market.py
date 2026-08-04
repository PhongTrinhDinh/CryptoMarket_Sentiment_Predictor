import ccxt
import logging
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import insert
from apps.db.database import SessionLocal, init_db
from apps.db.models import MarketData

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fetch_store_ohlcv(symbol: str = "BTC/USDT", timeframe: str = '15m', limit: int = 1000, since: int = None):
    exchange = ccxt.binance({
        'enableRateLimit': True,
    })
    
    # If since is not provided, default to approximately 30 days ago
    if since is None:
        since = exchange.milliseconds() - 30 * 24 * 60 * 60 * 1000
        
    all_ohlcv_data = []
    current_since = since
    
    try:
        logger.info(f"Fetching {timeframe} candles for {symbol} from {exchange.id} since {datetime.fromtimestamp(since/1000, tz=timezone.utc)}...")
        
        while True:
            ohlcv_data = exchange.fetch_ohlcv(symbol, timeframe, since=current_since, limit=limit)
            if not ohlcv_data:
                break
                
            all_ohlcv_data.extend(ohlcv_data)
            logger.info(f"Fetched {len(ohlcv_data)} candles. Total so far: {len(all_ohlcv_data)}")
            
            if len(ohlcv_data) < limit:
                break
                
            # Next request starts exactly after the last candle's timestamp
            current_since = ohlcv_data[-1][0] + 1
            
        if not all_ohlcv_data:
            logger.warning("No data returned from the exchange.")
            return
        
        records = []
        for candle in all_ohlcv_data:
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
        