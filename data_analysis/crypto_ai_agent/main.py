# main.py（或 Django view）

import os
import sys
import django

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cryptocurrency.settings")
django.setup()

from django.contrib.auth.models import User
from data_analysis.crypto_ai_agent.qa_agent import create_qa_function

user = User.objects.first()
qa = create_qa_function()

while True:
    q = input("請輸入問題 (q 離開): ").strip()
    if q.lower() == "q":
        break
    answer = qa(q, user)
    print("🧠 回答：", answer)
