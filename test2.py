import requests
from data_analysis.text_translator import translator
import time
#kaggle
url = 'https://9361-34-55-94-189.ngrok-free.app/predict'  # 請替換為 Ngrok 顯示的 URL

# 輸入問題
user_question = input("請輸入問題: ")

# 中文翻譯成英文
translated_question = translator.translate_to_english(user_question)
print(translated_question)

# 使用 api
start = time.time()
data = {"text": translated_question}
response = requests.post(url, json=data)
generated_answer = response.json()['response']
print(generated_answer)
end = time.time()
# 英文翻譯回中文
translated_answer = translator.translate_to_chinese(generated_answer)
print(translated_answer)

print("\n輸出結果：")
print(f"中文轉英文：\n{translated_question}\n\n")
print(f"llm(執行時間：{end - start:.4f}秒)：\n{generated_answer}\n\n")
print(f"英文翻譯回中文：\n{translated_answer}\n\n")