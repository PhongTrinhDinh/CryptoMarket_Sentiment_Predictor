from sqlalchemy import Column, Integer, String, Float, DateTime, Index
from datetime import datetime, timezone
from .database import Base

class MarketData(Base):
    __tablename__ = "marketdata"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('idx_symbol_timestamp', 'symbol', 'timestamp', unique=True),
    )
    
class NewsSentiment(Base):
    __tablename__ = "news_sentiment"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=True) # 'reddit', 'newsapi'
    entity = Column(String(50), nullable=True) # 'BTC', 'Crypto'
    published_at = Column(DateTime(timezone=True), nullable=True)
    
    content = Column(String, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    sentiment_reason = Column(String, nullable=True) # Why LLM judged this score?
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('idx_entity_published_at', 'entity', 'published_at'),
    )