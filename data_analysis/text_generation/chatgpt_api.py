from dotenv import load_dotenv
import os
from pathlib import Path
import requests

env_path = Path(__file__).resolve().parents[2] / '.env'
load_dotenv(dotenv_path=env_path)

api = os.getenv('API_KEY')
api2 = os.getenv('API_KEY2')


def call_chatgpt(system, text):
    """
    ✅ 主要使用 ChatAnywhere (api2)
    https://github.com/chatanywhere/GPT_API_free
    若失敗則自動改用 free.v36.cm (api)
    https://github.com/popjane/free_chatgpt_api
    """

    # --- 第一個主要 API (ChatAnywhere) ---
    url1 = "https://api.chatanywhere.org/v1/chat/completions"
    headers1 = {
        "Authorization": f"Bearer {api2}",
        "Content-Type": "application/json",
    }
    data1 = {
        "model": "gpt-5-mini",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": text},
        ],
    }

    # --- 備用 API (free.v36.cm) ---
    url2 = "https://free.v36.cm/v1/chat/completions"
    headers2 = {
        "Authorization": f"Bearer {api}",
        "Content-Type": "application/json",
    }
    data2 = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": text},
        ],
    }

    # 先試主要 API
    try:
        response = requests.post(url1, headers=headers1, json=data1, timeout=30)
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        return content

    except Exception as e1:
        print(f"⚠️ ChatAnywhere 失敗：{e1}")
        print("➡️ 改用備用 free.v36.cm...")

        try:
            response = requests.post(url2, headers=headers2, json=data2, timeout=30)
            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            return content

        except Exception as e2:
            return f"❌ 兩個 API 都失敗\nChatAnywhere 錯誤：{e1}\nfree.v36.cm 錯誤：{e2}"