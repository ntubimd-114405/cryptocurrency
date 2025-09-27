import os
import django
import sys

# 初始化 Django 環境
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cryptocurrency.settings")
django.setup()

from agent.models import Questionnaire
from data_analysis.text_generation.chatgpt_api import call_chatgpt

# 取得 id=7 的問卷
qnn = Questionnaire.objects.get(id=7)

# 準備問卷題目與選項文字
prompt = (
    "請幫我針對以下問卷選項進行「未來投資風險態度」的評估，"
    "並給予每個選項 1~5 分（1 = 最保守、風險最低，5 = 最激進、風險最高）：\n\n")
for question in qnn.questions.all():
    prompt += f"題目 {question.order}: {question.content} (類型: {question.get_question_type_display()})\n"
    for option in question.answer_options.all():
        prompt += f"   - 選項 {option.order}: {option.content}\n"
    prompt += "\n"

# 呼叫 GPT 分析
result = call_chatgpt("", prompt)

# 將結果存成 txt 檔案
output_path = os.path.join(os.path.dirname(__file__), "risk_assessment.txt")
with open(output_path, "w", encoding="utf-8") as f:
    f.write("=== 問卷風險評估結果 ===\n\n")
    f.write(prompt + "\n")
    f.write("=== GPT 生成的風險評分 ===\n\n")
    f.write(result)

print(f"風險評估完成，已輸出至: {output_path}")
