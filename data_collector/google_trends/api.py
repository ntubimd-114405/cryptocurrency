import pandas as pd
from pytrends.request import TrendReq

def trends(timeframe):
    # 建立 TrendReq 連線物件，設定介面語言為繁體中文，tz=0 代表使用 UTC 時區
    pytrends = TrendReq(hl='zh-TW', tz=0)

    # 設定要查詢的關鍵字
    keywords = ["Bitcoin", "BTC"]

    # 建立 payload，設定查詢時間範圍
    pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo='', gprop='')

    # 取得關鍵字的搜尋量趨勢資料
    data = pytrends.interest_over_time()

    if data.empty:
        return pd.DataFrame(columns=['date', 'full_value', 'abbreviated_value'])  # 避免回傳空 DataFrame 出錯

    # 將資料列保留為 full_value 和 abbreviated_value
    data['full_value'] = data[keywords[0]]  # 將第一個關鍵字的搜尋量作為 full_value
    data['abbreviated_value'] = data[keywords[1]]  # 將第二個關鍵字的搜尋量作為 abbreviated_value

    # 保留日期與 full_value 和 abbreviated_value 欄位
    data = data[['full_value', 'abbreviated_value']].reset_index()
    data.rename(columns={'date': 'date'}, inplace=True)  # 確保欄位名稱為 'date'

    return data

if __name__ == "__main__":
    print(trends("2020-01-01 2020-12-31"))
