# import_coindesk.py
import os
import django

# 設定 Django 環境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cryptocurrency.settings")
django.setup()

from report.views import generate_weekly_report2
generate_weekly_report2(2025, 42)
# for i in range(1,43):
#     generate_weekly_report2(2025, i)

