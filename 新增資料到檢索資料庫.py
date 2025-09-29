import os
import django

# 設定 Django 環境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cryptocurrency.settings")
django.setup()


from data_analysis.crypto_ai_agent.news_agent import initialize_news_vector_store

initialize_news_vector_store()
print("✅ 向量庫初始化完成")