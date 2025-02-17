import yfinance as yf

def finance(symbol, start_date="2020-01-01", end_date=None, interval="1d"):

    # 抓取每小時數據
    data = yf.download(symbol, start=start_date, end=end_date, interval=interval)
    
    # 顯示前幾行
    print(len(data))
    print(data.head(10))


if __name__ == "__main__":
    symbols = {
        "sp500": "^GSPC",   # S&P500 指數
        "gold": "GC=F",     # 黃金期貨
        "oil": "CL=F"  ,     # WTI 原油期貨
        "usd": "DX-Y.NYB", #美元指數
    }
    for k,v in symbols.items():
        finance(v)