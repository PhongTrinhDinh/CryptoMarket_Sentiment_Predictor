import sys
import os
from pathlib import Path
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as plotly_go
import plotly.express as px

# --- Path Setup ---
FILE = Path(__file__).resolve()
ROOT = FILE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from apps.db.database import SessionLocal
from apps.db.models import NewsSentiment
from apps.features.technical import get_technical_features

# --- API Configuration ---
API_URL = os.getenv("API_URL", "http://localhost:8000/predict")

st.set_page_config(page_title="Crypto Sentiment Predictor", layout="wide", page_icon="📈")

@st.cache_data(ttl=900) # Cache 15 minutes
def fetch_prediction(symbol="BTC/USDT", entity="BTC"):
    try:
        response = requests.get(f"{API_URL}?symbol={symbol}&entity={entity}")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Lỗi khi gọi API: {response.text}")
            return None
    except Exception as e:
        st.error(f"Lỗi kết nối API: {e}. Vui lòng kiểm tra xem FastAPI đã chạy chưa.")
        return None

def fetch_latest_news(entity="BTC", limit=10):
    db = SessionLocal()
    try:
        query = db.query(NewsSentiment).filter(NewsSentiment.entity == entity).order_by(NewsSentiment.published_at.desc()).limit(limit)
        news_df = pd.read_sql(query.statement, db.bind)
        return news_df
    except Exception as e:
        st.error(f"Lỗi khi tải tin tức từ DB: {e}")
        return pd.DataFrame()
    finally:
        db.close()

def main():
    st.title("📈 Crypto Market Sentiment & AI Predictor")
    
    # Header & Refresh
    col1, col2 = st.columns([1, 8])
    with col1:
        st.button("🔄 Làm mới dữ liệu", on_click=st.cache_data.clear)
            
    symbol = "BTC/USDT"
    entity = "BTC"
    
    # Fetch Data
    pred_data = fetch_prediction(symbol, entity)
    tech_data = get_technical_features(symbol, limit=100)
    news_df = fetch_latest_news(entity, limit=10)
    
    if pred_data and not tech_data.empty:
        # Calculate states
        current_close = tech_data['close'].iloc[-1]
        prev_close = tech_data['close'].iloc[-2]
        delta_price = current_close - prev_close
        
        label = pred_data.get("label", "Unknown")
        avg_sentiment = news_df['sentiment_score'].mean() if not news_df.empty else 0.0
        
        # --- 1. HERO SECTION ---
        st.markdown("### 1. Tín hiệu Hành động")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Giá hiện tại (Close)", f"${current_close:,.2f}", f"{delta_price:+,.2f}")
        with col_b:
            st.metric("Nhãn dự đoán (AI)", label)
        with col_c:
            st.metric("Điểm Sentiment (TB 10 tin)", f"{avg_sentiment:+.2f}")
            
        st.markdown("---")
        
        # --- 2. MODEL CONFIDENCE ---
        st.markdown("### 2. Cấu trúc Xác suất (Model Confidence)")
        probs = pred_data.get("probabilities", {})
        
        prob_df = pd.DataFrame({
            "Kịch bản": ["Tăng (Up)", "Đi ngang (Sideways)", "Giảm (Down)"],
            "Xác suất": [probs.get("up", 0), probs.get("sideways", 0), probs.get("down", 0)]
        })
        
        fig_prob = px.bar(prob_df, x="Kịch bản", y="Xác suất", text="Xác suất",
                          color="Kịch bản",
                          color_discrete_map={"Tăng (Up)": "green", "Đi ngang (Sideways)": "gray", "Giảm (Down)": "red"})
        fig_prob.update_traces(texttemplate='%{text:.1%}', textposition='outside')
        fig_prob.update_layout(yaxis_tickformat='.0%', showlegend=False, height=350, margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_prob, use_container_width=True)
        
        st.markdown("---")
        
        # --- 3. TECHNICAL CHART ---
        st.markdown("### 3. Biểu đồ Kỹ thuật (100 Nến gần nhất)")
        fig_candle = plotly_go.Figure()
        
        fig_candle.add_trace(plotly_go.Candlestick(
            x=tech_data.index,
            open=tech_data['open'],
            high=tech_data['high'],
            low=tech_data['low'],
            close=tech_data['close'],
            name='Candlestick'
        ))
        
        # Optional: Add Bollinger Bands if they exist in features
        if 'bb_upper' in tech_data.columns and 'bb_lower' in tech_data.columns:
            fig_candle.add_trace(plotly_go.Scatter(x=tech_data.index, y=tech_data['bb_upper'], line=dict(color='rgba(173,216,230,0.5)', width=1), name='Upper BB'))
            fig_candle.add_trace(plotly_go.Scatter(x=tech_data.index, y=tech_data['bb_lower'], line=dict(color='rgba(173,216,230,0.5)', width=1), fill='tonexty', name='Lower BB'))
            
        fig_candle.update_layout(xaxis_rangeslider_visible=False, height=500, margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_candle, use_container_width=True)
        
        st.markdown("---")
        
        # --- 4. SENTIMENT FEED ---
        st.markdown("### 4. Mạch truyện Cảm xúc (Sentiment Feed)")
        if not news_df.empty:
            for _, row in news_df.iterrows():
                score = row.get('sentiment_score', 0)
                emoji = "🟩" if score > 0 else "🟥" if score < 0 else "⬜"
                
                # Handling generic column names gracefully in case they differ slightly
                title = row.get('title', 'Không có tiêu đề')
                published_at = row.get('published_at', 'N/A')
                reason = row.get('sentiment_reason', row.get('content', 'Không có chi tiết'))
                url = row.get('url', '#')
                
                with st.expander(f"{emoji} [{published_at}] {title} (Điểm: {score})"):
                    st.markdown(f"**Lý do AI chấm điểm:**\n\n{reason}")
                    st.markdown(f"[🔗 Đọc bài viết gốc]({url})")
        else:
            st.info("Chưa có tin tức nào trong cơ sở dữ liệu.")
            
    else:
        st.warning("Đang chờ dữ liệu từ API hoặc DB. Đảm bảo Backend FastAPI đã hoạt động.")

if __name__ == "__main__":
    main()
