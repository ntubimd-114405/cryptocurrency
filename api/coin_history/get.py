import ccxt
from datetime import datetime, timezone

def get_history(coin):
    # 初始化交易所 Binance
    binance = ccxt.binance({
        'rateLimit': 1200,
        'enableRateLimit': True,
    })
    # 初始化交易所 Bitget
    bitget = ccxt.bitget({
        'rateLimit': 1200,
        'enableRateLimit': True,
    })

    # 設定交易對和時間間隔
    if coin == 'USDT':
        symbol = f'{coin}/DAI'  # 當 coin 是 'USDT' 時
    else:
        symbol = f'{coin}/USDT'  # 其他情況為 coin/USDT
    timeframe = '1d'  # K 線圖的時間間隔，例如 '1m', '5m', '1h', '1d'
    since = binance.parse8601('2025-1-1T00:00:00Z')  # 開始時間

    # 嘗試從 Binance 獲取歷史數據
    try:
        ohlcv = binance.fetch_ohlcv(symbol, timeframe, since)
    except:
        print(f"從 Binance 獲取資料失敗，嘗試使用 Bitget...")
        # 如果從 Binance 失敗，則嘗試從 Bitget 獲取資料
        try:
            ohlcv = bitget.fetch_ohlcv(symbol, timeframe, since)
        except:
            print(f"從 Bitget 獲取資料也失敗。")
            return None  # 如果兩個交易所都獲取失敗，返回 None

    data = []
    # 轉換數據為易讀格式
    for entry in ohlcv:
        timestamp, open_, high, low, close, volume = entry
        date = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        data.append([date, open_, high, low, close, volume])
    
    return data
