# main.py

import os
import sys
import django

# 初始化 Django 環境（從 crypto_ai_agent 向上兩層）
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
#BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".",))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cryptocurrency.settings")
django.setup()


from django.contrib.auth.models import User
from data_analysis.crypto_ai_agent.qa_agent import create_qa_function

# 取得使用者，假設使用第一位 user
user = User.objects.first()
print(user)
qa = create_qa_function()

while True:
    q = input("❓ 請輸入問題（輸入 q 離開）：").strip()
    if q.lower() == "q":
        break
    answer = qa(q, user)
    print("🧠 回答：", answer)



