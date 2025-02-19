import pandas as pd
from celery import shared_task

@shared_task
def macro_economy():
    from .models import Indicator,IndicatorValue
    from data_collector.macro_economy.fredapi_data import get_fred_data
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

    for k, v in indicators.items():     
        indicator, created = Indicator.objects.update_or_create(
            abbreviation=v,
            defaults={'name': k}  # 如果已存在，則更新 name
        )
              
        data = get_fred_data(v) 

        for date, value in data.items():  
            date = date.date() 
            if pd.notna(value):
                IndicatorValue.objects.get_or_create(
                    indicator=indicator, date=date, defaults={'value': value}
                )

        print(f"{k} 完成處理")