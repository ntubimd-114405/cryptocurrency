from fredapi import Fred
from pathlib import Path
from dotenv import load_dotenv
import os

def get_fred_data(series): #這個api還有多種資料還未開發 https://fred.stlouisfed.org/docs/api/fred/
    # 設定 .env 文件路徑
    env_path = Path(__file__).resolve().parents[2] / '.env'  # 上兩層目錄
    load_dotenv(dotenv_path=env_path)

    API_KEY = os.getenv('fred_api')  # 註冊後獲得
    fred = Fred(api_key=API_KEY)

    data = fred.get_series(series)

    # 返回最近5筆數據
    return data


# 使用函數並顯示結果
if __name__ == "__main__":
    indicators = {
    "國內生產總值 (GDP)": "GDP",
    "失業率": "UNRATE",
    "通脹率 (CPI)": "CPIAUCSL",
    "利率 (聯邦基金利率)": "FEDFUNDS",
    "貿易平衡": "NETEXP",
    "貨幣供應量 (M2)": "M2SL",
    "政府預算赤字/盈餘": "FYFSD",
    "生產者物價指數 (PPI)": "PPIACO",
    "消費者信心指數 (CCI)": "UMCSENT",
    }
    for k,v in indicators.items():
        print(k)
        a=get_fred_data(v)
        print(type(a))
        break
