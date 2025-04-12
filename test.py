from data_analysis.text_translator import translator
from data_analysis.text_generation import llm
#本地端
# 輸入問題
user_question = input("請輸入問題: ")

# 中文翻譯成英文
translated_question = translator.translate_to_english(user_question)
print(translated_question)

# 使用 finance-LLM
generated_answer = llm.generate_text_from_prompt(translated_question)
print(generated_answer)

# 英文翻譯回中文
translated_answer = translator.translate_to_chinese(generated_answer)
print(translated_answer)

print("\n輸出結果：")
print(f"中文轉英文：\n{translated_question}\n\n")
print(f"llm：\n{generated_answer}\n\n")
print(f"英文翻譯回中文：\n{translated_answer}\n\n")