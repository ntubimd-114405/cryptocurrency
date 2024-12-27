import ccxt
from datetime import datetime, timezone


def get_history(coin):
    exchange = ccxt.binance({
        'rateLimit': 1200,
        'enableRateLimit': True,
    })

    # 設定交易對和時間間隔
    if coin == 'USDT':
        symbol = f'{coin}/DAI'  # 當 coin 是 'USDT' 時
    else:
        symbol = f'{coin}/USDT'  # 其他情況為 coin/USDT
    timeframe = '1d'     # K 線圖的時間間隔，例如 '1m', '5m', '1h', '1d'
    since = exchange.parse8601('2024-12-26T00:00:00Z')  # 開始時間

    # 獲取歷史數據
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since)
    except:
        return None
    data=[]
    # 轉換數據為易讀格式
    for entry in ohlcv:
        timestamp, open_, high, low, close, volume = entry
        date = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        data.append([date,open_,high,low,close,volume])
    return data
