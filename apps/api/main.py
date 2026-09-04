import sys
import os
from pathlib import Path

FILE = Path(__file__).resolve()
ROOT = FILE.parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import numpy as np
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
import xgboost as xgb
import joblib
import pandas as pd

from apps.features.technical import get_technical_features
from apps.features.builder import get_aggregated_sentiment

MODEL_DIR = os.path.join(ROOT, 'apps', 'models', 'saved_models')
MODEL_PATH = os.path.join(MODEL_DIR, 'xgboost_model.json')
FEATURES_PATH = os.path.join(MODEL_DIR, 'features.joblib')

# Global variables to hold model and feature columns
model = None
feature_cols = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, feature_cols
    # Startup Event: Load model and features once into memory
    if os.path.exists(MODEL_PATH) and os.path.exists(FEATURES_PATH):
        model = xgb.XGBClassifier()
        model.load_model(MODEL_PATH)
        feature_cols = joblib.load(FEATURES_PATH)
        print("Model and features loaded successfully.")
    else:
        print("Model or features file not found. Prediction endpoint will return 503.")
    yield
    # Clean up (if any)
    model = None
    feature_cols = None

app = FastAPI(lifespan=lifespan)

@app.get("/predict")
def predict_sentiment(symbol: str = 'BTC/USDT', entity: str = 'BTC'):
    if model is None or feature_cols is None:
        raise HTTPException(status_code=503, detail="Model is not loaded. Train the model first.")
        
    try:
        # Fetch technical features (fetching a small window to calculate indicators correctly)
        df_tech = get_technical_features(symbol, limit=200)
        if df_tech.empty:
            raise HTTPException(status_code=404, detail="Not enough technical data.")
            
        df_sentiment = get_aggregated_sentiment(entity, limit=50)
        
        if not df_sentiment.empty:
            df_merged = df_tech.join(df_sentiment, how='left')
            df_merged['sentiment_score'] = df_merged['sentiment_score'].fillna(0.0)
        else:
            df_merged = df_tech.copy()
            df_merged['sentiment_score'] = 0.0
            
        # Get the latest row (iloc[-1]) for prediction
        latest_row = df_merged.iloc[[-1]]
        
        # Ensure only the trained features are passed to the model, in the right order
        for col in feature_cols:
            if col not in latest_row.columns:
                latest_row[col] = 0.0
                
        X = latest_row[feature_cols]
        X = X.select_dtypes(include=[np.number, bool])
        
        # Soft Probability: predict_proba returns probabilities for each class
        probs = model.predict_proba(X)[0] 
        
        # Map back to original logic in train_xgboost:
        # 0: Down (-1)
        # 1: Sideways (0)
        # 2: Up (1)
        prob_down = float(probs[0])
        prob_sideways = float(probs[1])
        prob_up = float(probs[2])
        
        predicted_class = int(np.argmax(probs))
        
        class_mapping = {0: -1, 1: 0, 2: 1}
        label_name = {0: "Down", 1: "Sideways", 2: "Up"}
        
        timestamp = str(latest_row.index[0]) if not latest_row.empty else None
        
        return {
            "symbol": symbol,
            "prediction": class_mapping[predicted_class],
            "label": label_name[predicted_class],
            "probabilities": {
                "down": prob_down,
                "sideways": prob_sideways,
                "up": prob_up
            },
            "timestamp": timestamp
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
