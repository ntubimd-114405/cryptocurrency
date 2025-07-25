# seed_feedback_questions.py

from main.models import FeedbackQuestion, FeedbackOption  # ← 替換為你的實際 app 名稱

questions_data = [
    {
        "text": "您是否有使用過本平台的「查詢貨幣資訊」功能？",
        "type": "radio",
        "options": ["是", "否"]
    },
    {
        "text": "您對於「新聞相關資料整合」功能是否滿意？",
        "type": "rating",
        "options": ["1", "2", "3", "4", "5"]
    },
    {
        "text": "您最常使用哪些功能？（可複選）",
        "type": "checkbox",
        "options": ["貨幣查詢", "新聞資料", "經濟指標", "報告生成功能", "問卷調查"]
    },
    {
        "text": "報告生成功能是否對您有幫助？",
        "type": "radio",
        "options": ["非常有幫助", "有一點幫助", "普通", "沒幫助"]
    },
    {
        "text": "您希望本平台新增哪些功能？",
        "type": "text",
        "options": []
    },
    {
        "text": "有哪些地方讓您使用上感到困擾？",
        "type": "text",
        "options": []
    },
    {
        "text": "在報告自動生成方面，您希望報告中包含哪些內容？",
        "type": "text",
        "options": []
    },
    {
        "text": "您對本平台的整體滿意度為何？",
        "type": "rating",
        "options": ["1", "2", "3", "4", "5"]
    },
    {
        "text": "您會推薦本平台給其他人使用嗎？",
        "type": "radio",
        "options": ["會", "不會", "不確定"]
    },
    {
        "text": "請留下您願意提供的改善建議",
        "type": "text",
        "options": []
    },
]

def seed_feedback_questions():
    created_count = 0

    for q in questions_data:
        # 檢查題目是否已存在
        question, created = FeedbackQuestion.objects.get_or_create(
            text=q["text"],
            defaults={"question_type": q["type"], "required": True}
        )

        if created:
            created_count += 1
            print(f"✅ 新增題目：{q['text']}")
        else:
            print(f"⚠️ 題目已存在：{q['text']}")

        # 加入選項（如果有的話），並檢查是否已存在
        for option_text in q["options"]:
            if not question.options.filter(text=option_text).exists():
                FeedbackOption.objects.create(question=question, text=option_text)
                print(f"   ➕ 新增選項：{option_text}")
            else:
                print(f"   ⚠️ 選項已存在：{option_text}")

    print(f"\n共新增 {created_count} 筆新題目")
