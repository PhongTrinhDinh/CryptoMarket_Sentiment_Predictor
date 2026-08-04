import pytest
from unittest.mock import patch, MagicMock
import sys
import pandas as pd

from scripts.run import run_ingestion, run_sentiment, run_features, main

@patch("scripts.run.fetch_store_ohlcv")
@patch("scripts.run.fetch_crypto_news")
def test_run_ingestion(mock_fetch_news, mock_fetch_ohlcv):
    """Test the run_ingestion pipeline function."""
    run_ingestion()
    mock_fetch_ohlcv.assert_called_once_with(symbol='BTC/USDT', timeframe='15m')
    mock_fetch_news.assert_called_once_with(query='Bitcoin OR BTC', target_entity="BTC")

@patch("scripts.run.analyze_update_sentiments")
def test_run_sentiment(mock_analyze):
    """Test the run_sentiment pipeline function."""
    run_sentiment()
    mock_analyze.assert_called_once_with(limit=500)

@patch("scripts.run.build_training_dataset")
def test_run_features(mock_build_dataset):
    """Test the run_features pipeline function."""
    # Mock a non-empty dataframe
    mock_df = MagicMock(spec=pd.DataFrame)
    mock_df.empty = False
    mock_df.shape = (10, 5)
    mock_build_dataset.return_value = mock_df
    
    run_features()
    mock_build_dataset.assert_called_once_with(symbol='BTC/USDT', entity='BTC', lookahead_candless=4)

@patch("scripts.run.init_db")
@patch("scripts.run.run_ingestion")
@patch("scripts.run.run_sentiment")
@patch("scripts.run.run_features")
def test_main_all(mock_features, mock_sentiment, mock_ingestion, mock_init_db):
    """Test the main entrypoint with the 'all' task."""
    test_args = ["run.py", "--task", "all"]
    with patch.object(sys, 'argv', test_args):
        main()
        
    mock_init_db.assert_called_once()
    mock_ingestion.assert_called_once()
    mock_sentiment.assert_called_once()
    mock_features.assert_called_once()

@patch("scripts.run.init_db")
@patch("scripts.run.run_ingestion")
@patch("scripts.run.run_sentiment")
@patch("scripts.run.run_features")
def test_main_ingest(mock_features, mock_sentiment, mock_ingestion, mock_init_db):
    """Test the main entrypoint with the 'ingest' task."""
    test_args = ["run.py", "--task", "ingest"]
    with patch.object(sys, 'argv', test_args):
        main()
        
    mock_init_db.assert_called_once()
    mock_ingestion.assert_called_once()
    mock_sentiment.assert_not_called()
    mock_features.assert_not_called()

@patch("scripts.run.init_db")
@patch("scripts.run.run_ingestion")
@patch("scripts.run.run_sentiment")
@patch("scripts.run.run_features")
def test_main_sentiment(mock_features, mock_sentiment, mock_ingestion, mock_init_db):
    """Test the main entrypoint with the 'sentiment' task."""
    test_args = ["run.py", "--task", "sentiment"]
    with patch.object(sys, 'argv', test_args):
        main()
        
    mock_init_db.assert_called_once()
    mock_ingestion.assert_not_called()
    mock_sentiment.assert_called_once()
    mock_features.assert_not_called()

@patch("scripts.run.init_db")
@patch("scripts.run.run_ingestion")
@patch("scripts.run.run_sentiment")
@patch("scripts.run.run_features")
def test_main_features(mock_features, mock_sentiment, mock_ingestion, mock_init_db):
    """Test the main entrypoint with the 'features' task."""
    test_args = ["run.py", "--task", "features"]
    with patch.object(sys, 'argv', test_args):
        main()
        
    mock_init_db.assert_called_once()
    mock_ingestion.assert_not_called()
    mock_sentiment.assert_not_called()
    mock_features.assert_called_once()
