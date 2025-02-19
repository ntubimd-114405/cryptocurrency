import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
import os


def predict_crypto_price(data):
    # 設定模型路徑
    model_path = os.path.join(os.path.dirname(__file__), "1_Market_lstm_model.h5")
    model = load_model(model_path)
    
    # 選擇特徵
    features = ['close_price', 'high_price', 'low_price', 'open_price', 'volume']
    df = data[features].copy()
    
    # 標準化數據
    scaler = MinMaxScaler()
    df_scaled = scaler.fit_transform(df)
    
    # 構建輸入數據
    input_data = np.array(df_scaled[-24:])  # 取最近 24 小時的數據
    input_data = input_data.reshape(1, 24, len(features))  # LSTM 需要 (samples, timesteps, features)
    
    # 預測
    predicted_scaled = model.predict(input_data)
    
    # 反標準化
    predicted_price = scaler.inverse_transform(
        np.hstack([predicted_scaled.reshape(1, -1), np.zeros((1, 4))])
    )[0, 0]
    
    return predicted_price

if __name__ == "__main__":
    # 測試用範例數據
    sample_data = pd.DataFrame({
        "close_price": np.random.rand(50) * 50000,
        "high_price": np.random.rand(50) * 51000,
        "low_price": np.random.rand(50) * 49000,
        "open_price": np.random.rand(50) * 50000,
        "volume": np.random.rand(50) * 1000
    })
    
    predicted_price = predict_crypto_price(sample_data)
    print(f"Predicted Price: {predicted_price}")
