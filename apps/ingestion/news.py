import sys
from pathlib import Path

FILE = Path(__file__).resolve()
ROOT = FILE.parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import os
import requests
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

from apps.db.database import SessionLocal, init_db
from apps.db.models import NewsSentiment

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

def fetch_crypto_news(query: str = "Bitcoin OR BTC", target_entity="BTC"):
    api_key = os.getenv("NEWSAPI_KEY")
    if not api_key:
        logger.error("NEWSAPI_KEY has not been configured in the .env file!")
        return
    
    db = SessionLocal()
    new_records = []
    
    try:
        # Loop for approximately 5 pages (500 most recent items)
        for page in range(1, 6):
            url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&language=en&pageSize=100&page={page}&apiKey={api_key}"
            
            logger.info(f"Fetching news related to '{query}' from NewsAPI (Page {page})...")
            response = requests.get(url)
            data = response.json()
            
            if data.get("status") != "ok":
                # Some API limits might trigger an error instead of just returning empty
                if data.get("code") == "maximumResultsReached":
                    logger.warning("Reached maximum results allowed by NewsAPI for this plan.")
                    break
                logger.error(f"Error from NewsAPI: {data.get('message')}")
                break
            
            articles = data.get("articles", [])
            if not articles:
                break
            
            for item in articles:
                published_str = item.get("publishedAt")
                if not published_str:
                    continue
                    
                pub_time = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
                
                title = item.get("title", "")
                description = item.get("description", "")
                full_content = f"{title}. {description}"
                
                exists = db.query(NewsSentiment.id).filter(
                    NewsSentiment.published_at == pub_time,
                    NewsSentiment.source == item.get("source", {}).get("name", "newsapi")
                ).first()
                
                if not exists:
                    new_records.append(
                        NewsSentiment(
                            source=item.get("source", {}).get("name", "NewsAPI")[:50],
                            entity=target_entity,
                            published_at=pub_time,
                            content=full_content[:2000],
                            sentiment_score=0.0,
                            sentiment_reason="Not yet analyzed"
                        )
                    )
        
        if new_records:
            db.add_all(new_records)
            db.commit()
            logger.info(f"Successfully saved {len(new_records)} new articles from NewsAPI.")
        else:
            logger.info("There are no new articles.")
            
    except Exception as e:
        logger.error(f"Error processing news data: {e}")
    finally:
        db.close()
        