import os
import django

# 設定 Django 環境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cryptocurrency.settings")
django.setup()
from main.tasks import fetch_coin_history
for i in range(208,559):
    fetch_coin_history(i)