import yfinance as yf
from datetime import datetime, timezone
import time
import pandas as pd

# 8-2 Yahoo Finance
def get_finance(symbol, start_date=None, interval="1d", max_retry=3):
    """
    從 Yahoo Finance 下載資料，支援自動重試與避免被封鎖
    """
    # 轉換 start_date 為 UTC aware datetime
    if start_date and isinstance(start_date, str):
        start_date = pd.to_datetime(start_date).tz_localize(timezone.utc)
    elif start_date and isinstance(start_date, datetime) and start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)

    # 判斷是否在未來
    today_utc = datetime.now(timezone.utc)
    if start_date and start_date >= today_utc:
        print(f"⚠️ {symbol} start_date 在未來，跳過下載")
        return None

    for attempt in range(max_retry):
        try:
            data = yf.download(
                symbol,
                start=start_date,
                interval=interval,
                progress=False,
                threads=False,      # 避免多線程封鎖
                auto_adjust=False   # 原始價格，若需調整改 True
            )
            if data.empty:
                print(f"⚠️ {symbol} 返回空資料")
            return data
        except Exception as e:
            print(f"❌ {symbol} 下載失敗，重試 {attempt+1}/{max_retry}: {e}")
            time.sleep(5)
    print(f"❌ {symbol} 最終下載失敗")
    return None

if __name__ == "__main__":
    symbols = {
        "VIX": "^VIX", 
        "sp500": "^GSPC",
        "gold": "GC=F",
        "oil": "CL=F",
        "usd": "DX-Y.NYB",
    }

    all_data = {}
    for k, v in symbols.items():
        df = get_finance(v, start_date="2025-01-01")
        if df is not None and not df.empty:
            print(f"{k} 資料列數: {len(df)}")
            print(df.head())
            all_data[k] = df
        time.sleep(5)  # 避免被 Yahoo Finance 限制


