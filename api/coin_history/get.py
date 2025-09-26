import ccxt
from datetime import datetime, timezone
import time

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

    # 設定交易對
    if coin.upper() == 'USDT':
        symbol = f'{coin}/DAI'
    else:
        symbol = f'{coin}/USDT'

    timeframe = '1d'  # K 線圖的時間間隔
    limit = 1000      # 單次抓取最多 1000 根 K 線
    since = binance.parse8601('2025-09-23T00:00:00Z')  # 開始時間

    all_data = []

    while True:
        try:
            ohlcv = binance.fetch_ohlcv(symbol, timeframe, since, limit)
        except:
            print(f"從 Binance 獲取資料失敗，嘗試使用 Bitget...")
            try:
                ohlcv = bitget.fetch_ohlcv(symbol, timeframe, since, limit)
            except:
                print(f"從 Bitget 獲取資料也失敗。")
                break  # 兩個交易所都失敗，停止抓取

        if not ohlcv:
            break  # 已抓完所有資料，停止迴圈

        for entry in ohlcv:
            timestamp, open_, high, low, close, volume = entry
            date = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            all_data.append([date, open_, high, low, close, volume])

        # 更新 since 到最後一筆時間 + 1 毫秒
        since = ohlcv[-1][0] + 1

        time.sleep(0.2)  # 避免請求過快

    return all_data
