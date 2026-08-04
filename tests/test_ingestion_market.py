import pytest
from unittest.mock import patch, MagicMock
import ccxt

from apps.ingestion.market import fetch_store_ohlcv

@patch("apps.ingestion.market.SessionLocal")
@patch("apps.ingestion.market.ccxt.binance")
def test_fetch_store_ohlcv_success(mock_binance_class, mock_session_local):
    """Test successful fetching and storing of OHLCV data."""
    # Setup mock exchange
    mock_exchange = MagicMock()
    mock_binance_class.return_value = mock_exchange
    
    # Setup mock data: [timestamp, open, high, low, close, volume]
    mock_exchange.fetch_ohlcv.side_effect = [
        [
            [1627804800000, 40000.0, 41000.0, 39000.0, 40500.0, 100.0],
            [1627805700000, 40500.0, 41500.0, 40000.0, 41000.0, 150.0]
        ],
        [] # Empty list on second call to break the loop
    ]
    
    # Setup mock database session
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db
    
    # Call the function
    fetch_store_ohlcv(symbol="BTC/USDT", timeframe="15m", limit=2)
    
    # Assert exchange was called correctly
    mock_binance_class.assert_called_once_with({'enableRateLimit': True})
    assert mock_exchange.fetch_ohlcv.call_count == 2
    
    # Assert database operations
    mock_db.execute.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.close.assert_called_once()

@patch("apps.ingestion.market.SessionLocal")
@patch("apps.ingestion.market.ccxt.binance")
def test_fetch_store_ohlcv_no_data(mock_binance_class, mock_session_local):
    """Test behavior when the exchange returns no data."""
    mock_exchange = MagicMock()
    mock_binance_class.return_value = mock_exchange
    mock_exchange.fetch_ohlcv.return_value = []
    
    fetch_store_ohlcv()
    
    mock_exchange.fetch_ohlcv.assert_called_once()
    # Database session shouldn't even be created if there's no data
    mock_session_local.assert_not_called()

@patch("apps.ingestion.market.SessionLocal")
@patch("apps.ingestion.market.ccxt.binance")
def test_fetch_store_ohlcv_db_error(mock_binance_class, mock_session_local):
    """Test rollback and graceful handling of database errors."""
    mock_exchange = MagicMock()
    mock_binance_class.return_value = mock_exchange
    mock_exchange.fetch_ohlcv.return_value = [
        [1627804800000, 40000.0, 41000.0, 39000.0, 40500.0, 100.0]
    ]
    
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db
    # Make db.execute raise an exception
    mock_db.execute.side_effect = Exception("Database connection error")
    
    fetch_store_ohlcv()
    
    mock_db.execute.assert_called_once()
    mock_db.rollback.assert_called_once()
    mock_db.commit.assert_not_called()
    mock_db.close.assert_called_once()

@patch("apps.ingestion.market.SessionLocal")
@patch("apps.ingestion.market.ccxt.binance")
def test_fetch_store_ohlcv_api_error(mock_binance_class, mock_session_local):
    """Test graceful handling of CCXT API errors."""
    mock_exchange = MagicMock()
    mock_binance_class.return_value = mock_exchange
    mock_exchange.fetch_ohlcv.side_effect = ccxt.NetworkError("Network error")
    
    # Should handle the exception gracefully without propagating
    fetch_store_ohlcv()
    
    mock_exchange.fetch_ohlcv.assert_called_once()
    mock_session_local.assert_not_called()
