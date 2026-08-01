import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from apps.db.database import Base, init_db, get_db
from apps.db.models import MarketData, NewsSentiment

# Create an in-memory SQLite database for testing models
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="module")
def test_engine():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_session(test_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_models_exist(test_engine):
    """Test that the tables for our models are successfully created."""
    inspector = inspect(test_engine)
    tables = inspector.get_table_names()
    assert "marketdata" in tables
    assert "news_sentiment" in tables

def test_market_data_insert(test_session):
    """Test inserting and retrieving a MarketData record."""
    now = datetime.now(timezone.utc)
    market_data = MarketData(
        symbol="BTC",
        timestamp=now,
        open=50000.0,
        high=51000.0,
        low=49000.0,
        close=50500.0,
        volume=100.5
    )
    test_session.add(market_data)
    test_session.commit()
    
    fetched = test_session.query(MarketData).filter_by(symbol="BTC").first()
    assert fetched is not None
    assert fetched.open == 50000.0
    assert fetched.volume == 100.5

def test_news_sentiment_insert(test_session):
    """Test inserting and retrieving a NewsSentiment record."""
    now = datetime.now(timezone.utc)
    news = NewsSentiment(
        source="newsapi",
        entity="BTC",
        published_at=now,
        content="Bitcoin is going up!",
        sentiment_score=0.9,
        sentiment_reason="Positive language"
    )
    test_session.add(news)
    test_session.commit()
    
    fetched = test_session.query(NewsSentiment).filter_by(entity="BTC").first()
    assert fetched is not None
    assert fetched.source == "newsapi"
    assert fetched.sentiment_score == 0.9
    assert fetched.sentiment_reason == "Positive language"

@patch("apps.db.database.SessionLocal")
def test_get_db_generator(mock_session_local):
    """Test the get_db generator correctly yields and closes a session."""
    mock_session = MagicMock()
    mock_session_local.return_value = mock_session
    
    gen = get_db()
    session = next(gen)
    
    assert session == mock_session
    mock_session.close.assert_not_called()
    
    try:
        next(gen)
    except StopIteration:
        pass
    else:
        pytest.fail("Generator did not stop as expected")
        
    mock_session.close.assert_called_once()

@patch("apps.db.database.engine")
@patch("apps.db.database.Base.metadata.create_all")
def test_init_db(mock_create_all, mock_engine):
    """Test the init_db function creates tables and executes hypertable setup."""
    mock_conn = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_conn
    
    init_db()
    
    # Assert create_all was called with the correct bind
    mock_create_all.assert_called_once_with(bind=mock_engine)
    
    # Assert a connection was made and a query was executed and committed
    mock_engine.connect.assert_called_once()
    mock_conn.execute.assert_called_once()
    mock_conn.commit.assert_called_once()
