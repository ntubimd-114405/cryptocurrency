import ccxt
from datetime import datetime, timezone

class CryptoHistoryFetcher:
    def __init__(self, coin,starttime):
        self.coin = coin
        self.exchange = ["binance", "bitget", "coinbasepro", "kraken", "bitfinex", "kucoin", "huobi", "okx", "bybit", "bitstamp"]
        self.symbol = self.get_symbol(coin)
        self.timeframe = '1m'  # K 線圖的時間間隔，例如 '1m', '5m', '1h', '1d'
        self.starttime = starttime

    def get_symbol(self, coin):
        if coin == 'USDT':
            return f'{coin}/DAI'  # 如果 coin 是 'USDT'
        else:
            return f'{coin}/USDT'  # 其他情況是 coin/USDT

    def get_history(self):
        for ex_name in self.exchange:
            try:
                # 獲取交易所實例
                exchange_instance = getattr(ccxt, ex_name)({
                    'rateLimit': 1200,
                    'enableRateLimit': True,
                })
                
                # 使用交易所的 fetch_ohlcv 方法獲取歷史數據
                starttime_iso = self.starttime.strftime('%Y-%m-%dT%H:%M:%SZ')
                since = exchange_instance.parse8601(starttime_iso)  # 開始時間
                ohlcv = exchange_instance.fetch_ohlcv(self.symbol, self.timeframe, since)
                break
            except:
                print(f"{self.coin}從 {ex_name} 獲取資料失敗")
                continue

        data = []
        # 轉換數據為易讀格式
        for entry in ohlcv:
            timestamp, open_, high, low, close, volume = entry
            date = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            data.append([date, open_, high, low, close, volume])
        
        return data
