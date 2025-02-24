import yfinance as yf
from datetime import datetime, timezone

def get_finance(symbol, start_date, interval="1d"):
    
    # 获取当前 UTC 时间
    today_utc = datetime.now(timezone.utc).date()
    if start_date >= today_utc:
        return None
    
    data = yf.download(symbol, start=start_date, interval=interval, progress=False)
    return data

if __name__ == "__main__":
    symbols = {
        "VIX": "^VIX", 
        "sp500": "^GSPC",   # S&P500 指數
        "gold": "GC=F",     # 黃金期貨
        "oil": "CL=F",      # WTI 原油期貨
        "usd": "DX-Y.NYB",  # 美元指數
    }
    for k, v in symbols.items():
        print(get_finance(v))
        break
