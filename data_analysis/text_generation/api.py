import requests
from data_analysis.text_translator import translator
from pathlib import Path
import os
from dotenv import load_dotenv


def finance_LLM_api(user_question):
    env_path = Path(__file__).resolve().parents[2] / '.env'  # 上兩層目錄
    load_dotenv(dotenv_path=env_path)
    API_URL = os.getenv('API_URL')+'/predict'

    # 中文翻譯成英文
    translated_question = translator.translate_to_english(user_question)

    data = {"text": translated_question}
    response = requests.post(API_URL, json=data)
    generated_answer = response.json()['response']

    # 英文翻譯回中文
    translated_answer = translator.translate_to_chinese(generated_answer)

    return translated_answer
