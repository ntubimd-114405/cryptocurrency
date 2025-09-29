import os
import django

# 設定 Django 環境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cryptocurrency.settings")
django.setup()

# 執行你的測試函數
from main.tasks import fetch_coin_history,fetch_and_store_coin_data
from news.tasks import news_crawler, news_sentiment,initialize_news_vector_store,news_summary
from other.tasks import save_financial,update_bitcoin_metrics,macro_economy


for i in range(1,4):
    fetch_coin_history(i)

fetch_and_store_coin_data()

news_crawler()
news_sentiment()
news_summary()
initialize_news_vector_store()

save_financial()
update_bitcoin_metrics()
macro_economy()

