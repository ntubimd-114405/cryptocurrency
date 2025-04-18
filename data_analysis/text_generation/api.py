import requests
from data_analysis.text_translator import translator

def finance_LLM_api(user_question):

    url = 'https://1aaf-34-148-5-244.ngrok-free.app/predict'  # 請替換為 Ngrok 顯示的 URL

    # 中文翻譯成英文
    translated_question = translator.translate_to_english(user_question)

    data = {"text": translated_question}
    response = requests.post(url, json=data)
    generated_answer = response.json()['response']

    # 英文翻譯回中文
    translated_answer = translator.translate_to_chinese(generated_answer)

    return translated_answer