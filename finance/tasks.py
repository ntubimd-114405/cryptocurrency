from django.utils import timezone
from celery import shared_task
from data_collector.fin.financial_data import get_finance
from .models import FinancialSymbol, FinancialData
from datetime import datetime
@shared_task
def save_financial():
    symbols = {
        "S&P 500 指數": "^GSPC",   # S&P500 指數
        "黃金期貨": "GC=F",         # 黃金期貨
        "WTI 原油期貨": "CL=F",     # WTI 原油期貨
        "美元指數": "DX-Y.NYB",    # 美元指數
        "VIX波動率指數": "^VIX", 
    }

    for name, sym in symbols.items():
        # 確保 FinancialSymbol 存在
        financial_symbol, created = FinancialSymbol.objects.get_or_create(
            symbol=sym,
            defaults={'name': name}
        )

        # 找到 FinancialData 最後的日期
        last_data = FinancialData.objects.filter(symbol=financial_symbol).order_by('date').last()
        if last_data:
            start_date = last_data.date + timezone.timedelta(days=1)
        else:
            start_date = datetime(2020, 1, 1)  # 若沒有數據則設為2020-01-01

        # 獲取金融數據
        data = get_finance(sym, start_date)
        # 儲存或更新 FinancialData
        if data is not None:
            for index, row in data.iterrows():
                FinancialData.objects.update_or_create(
                    symbol=financial_symbol,
                    date=index.date(),  # 使用索引中的日期
                    defaults={
                        'open_price': float(row['Open'].iloc[0]),  # 使用 .iloc[0]
                        'high_price': float(row['High'].iloc[0]),
                        'low_price': float(row['Low'].iloc[0]),
                        'close_price': float(row['Close'].iloc[0]),
                        'volume': int(row['Volume'].iloc[0]),      # 使用 .iloc[0]
                    }
                )
                print(f"{financial_symbol}更新{len(data)}筆")
        else:
            print(f"{financial_symbol}更新0筆")


'''
from finance.tasks import save_financial
save_financial()
'''