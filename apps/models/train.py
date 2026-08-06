import sys
import os
from pathlib import Path

FILE = Path(__file__).resolve()
ROOT = FILE.parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
    
import logging
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib

from apps.features.builder import build_training_dataset

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)c -%(message)s')
logger = logging.getLogger(__name__)

MODEL_DIR = os.path.join(ROOT, 'apps', 'models', 'saved_models')
os.makedirs(MODEL_DIR, exist_ok=True)

def train_xgboost():
    logger.info('Loading dataset from Features Builder...')
    df = build_training_dataset(symbol='BTC/USDT', entity='BTC', lookahead_candless=4)
    if df.empty or len(df) < 100:
        logger.error('Insufficient data for training. Please run further ingestion.')
        return 
    
    label_mapping = {-1: 0, 0: 1, 1: 2}
    df['target_label'] = df['target_label'].map(label_mapping)
    
    cols_to_drop = ['target_label']
    if 'created_at' in df.columns:
        cols_to_drop.append('created_at')
        
    X = df.drop(columns=cols_to_drop)
    X = X.select_dtypes(include=[np.number, bool]) # Ensure only numeric/boolean features are used
    y = df['target_label']
    
    logger.info(f'Total number of data points: {len(X)}')
    logger.info(f'Using features: {list(X.columns)}')
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    
    logger.info('Training Model...')
    logger.info(f'Train set size: {len(X_train.shape)}')
    logger.info(f'Test set size: {len(X_test.shape)}')
    
    model = xgb.XGBClassifier(
        objective='multi:softprob',
        num_class=3,
        max_depth=5,
        learning_rate=0.05,
        n_estimators=200,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42
    )
    
    model.fit(
        X_train, y_train,
        eval_set=[(X_train, y_train), (X_test, y_test)],
        verbose=50
    )
    
    logger.info('Evaluating the model on the test set...')
    y_pred = model.predict(X_test)
    
    acc = accuracy_score(y_test, y_pred)
    logger.info(f'Accuracy: {acc*100:.2f}%')
    
    print('\n--- CLASSIFICATION REPORT ---')
    target_names = ['Down (-1)', 'Sideways (0)', 'Up (1)']
    print(classification_report(y_test, y_pred, target_names=target_names, zero_division=0))
    
    model_path = os.path.join(MODEL_DIR, 'xgboost_model.json')
    model.save_model(model_path)
    
    features_path = os.path.join(MODEL_DIR, 'features.joblib')
    joblib.dump(list(X.columns), features_path)
    
    logger.info(f'Model saved at: {model_path}')
    logger.info(f'Training process completed!')
    
if __name__=='__main__':
    train_xgboost()