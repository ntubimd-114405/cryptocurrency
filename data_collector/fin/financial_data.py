import yfinance as yf
from datetime import datetime, timezone,timedelta
import time
import pandas as pd

# 8-2 Yahoo Finance
def get_finance(symbol, start_date=None, interval="1d", max_retry=3, max_days=30):
    """
    從 Yahoo Finance 下載資料，支援自動重試與避免被封鎖
    限制最大下載天數區間，避免時間範圍過大
    """

    # 轉換 start_date 為 UTC aware datetime
    if start_date and isinstance(start_date, str):
        start_date = pd.to_datetime(start_date).tz_localize(timezone.utc)
    elif start_date and isinstance(start_date, datetime) and start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)

    today_utc = datetime.now(timezone.utc)

    # 起始日期不可在未來
    if start_date and start_date >= today_utc:
        print(f"⚠️ {symbol} start_date 在未來，跳過下載")
        return None

    # 限制最大時間區間（例如180天）
    if start_date and (today_utc - start_date).days > max_days:
        start_date = today_utc - timedelta(days=max_days)
        print(f"⚠️ {symbol} start_date 超過最大允許範圍，使用修正後日期: {start_date}")

    for attempt in range(max_retry):
        try:
            data = yf.download(
                symbol,
                start=start_date,
                interval=interval,
                progress=False,
                threads=False,
                auto_adjust=False
            )
            if data.empty:
                print(f"⚠️ {symbol} 返回空資料")
            return data
        except Exception as e:
            print(f"❌ {symbol} 下載失敗，重試 {attempt+1}/{max_retry}: {e}")
            time.sleep(5)

    print(f"❌ {symbol} 最終下載失敗")
    return
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


