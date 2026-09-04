import sys
from pathlib import Path

FILE = Path(__file__).resolve()
ROOT = FILE.parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
    
import logging
import instructor
from openai import OpenAI
from pydantic import BaseModel, Field
from apps.db.database import SessionLocal
from apps.db.models import NewsSentiment

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "ollama")
LLM_MODEL = os.getenv("LLM_MODEL", "gemma4:e2b")

client = instructor.from_openai(
    OpenAI(
        base_url=OPENAI_BASE_URL,
        api_key=OPENAI_API_KEY
    ),
    mode=instructor.Mode.JSON
)

class SentimentResult(BaseModel):
    score: float = Field(
        description="Sentiment scores range from -1.0 (very negative) to 1.0 (very positive), with 0.0 being neutral. Please provide a detailed score to two decimal places (e.g., 0.25, -0.80)."
    )
    reason: str = Field(
        description="Briefly explain (in fewer than 20 words) the reason for this score."
    )
    
def analyze_update_sentiments(limit: int = 10):
    db = SessionLocal()
    try:
        unprocessed_news = db.query(NewsSentiment).filter(
            NewsSentiment.sentiment_reason == "Not yet analyzed"
        ).limit(limit).all()
        
        if not unprocessed_news:
            logger.info("There is no news requiring sentiment analysis.")
            return
        
        logger.info(f"Analyzing sentiment for {len(unprocessed_news)} articles using model {LLM_MODEL}...")
        
        for article in unprocessed_news:
            prompt = f"""
            You are a quantitative analyst specializing in the cryptocurrency market.
            Please read the following article title and summary, and assess its short-term impact on the price of {article.entity}.
            
            Article: {article.content}
            """
            
            try:
                response = client.chat.completions.create(
                    model=LLM_MODEL,
                    response_model=SentimentResult,
                    messages=[
                        {"role": "system", "content": "You are a JSON extraction system. Return only valid JSON matching the requested structure; do not provide explanations or output any markdown text outside of the JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0
                )
                
                article.sentiment_score = response.score
                article.sentiment_reason = response.reason
                
                logger.info(f"[ID: {article.id}] Score: {response.score} | Reason: {response.reason}")
                
                # Tạm nghỉ 3 giây giữa mỗi request để tránh lỗi HTTP 429 (Too Many Requests) của gói API miễn phí
                import time
                time.sleep(3)
            
            except Exception as e:
                logger.error(f"Error calling LLM for article ID {article.id}: {e}")
            
        db.commit()
        logger.info("Sentiment score updated successfully!")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Database Error: {e}")
    finally:
        db.close()
