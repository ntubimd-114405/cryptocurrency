from django.shortcuts import render

# agent/views.py
import requests
import hashlib

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from dotenv import load_dotenv
from datetime import datetime, timedelta
import os
from pathlib import Path
from django.db import connection
from django.conf import settings

env_path = Path(__file__).resolve().parents[2] / '.env'

# 加載 .env 檔案
load_dotenv(dotenv_path=env_path)

api = os.getenv('OPEN_API')

def call_free_chatgpt_api(request):
    
     # ➤ 產生 GPT prompt
    user_prompt = f"""
        我是一位「{1}」投資人，我的投資目標是「{2}」，
        我的總預算是 {4} 元，單一幣最大容忍為 {3} 元，
        投資經驗「{5}」，偏好幣種為「{6}」。
        請提供一份個人化的資產配置建議，並說明理由。
        """

    # ✅ 使用你申請到的 URL 和 API KEY
    url = 'https://free.v36.cm/v1/chat/completions'
    headers = {
        'Authorization': 'Bearer sk-f1VURcs4pENfXVMwCc1953E5717a4f33A7DcBd2c3133F71c',
        'Content-Type': 'application/json',
    }

    # 要送出的訊息內容
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": user_prompt}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return JsonResponse(result)
    
    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': str(e)}, status=500)
    
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Questionnaire, Question, AnswerOption, UserAnswer, UserQuestionnaireRecord

@login_required
def questionnaire_detail(request, questionnaire_id):
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)
    questions = questionnaire.questions.all().prefetch_related('answer_options')

    user = request.user

    if request.method == 'POST':
        user = request.user
        # 建立問卷填寫紀錄（或更新完成時間）
        record, created = UserQuestionnaireRecord.objects.get_or_create(
            user=user,
            questionnaire=questionnaire,
        )
        record.completed_at = timezone.now()
        record.save()

        for question in questions:
            # POST 傳入的欄位名稱
            field_name = f"question_{question.id}"
            user_answer, created = UserAnswer.objects.get_or_create(
                user=user,
                question=question,
            )
            # 先清空先前選項（多選用）
            user_answer.selected_options.clear()

            if question.question_type == Question.SINGLE_CHOICE:
                option_id = request.POST.get(field_name)
                if option_id:
                    try:
                        option = question.answer_options.get(id=option_id)
                        user_answer.selected_options.add(option)
                    except AnswerOption.DoesNotExist:
                        pass
                user_answer.save()

            elif question.question_type == Question.MULTIPLE_CHOICE:
                option_ids = request.POST.getlist(field_name)
                for option_id in option_ids:
                    try:
                        option = question.answer_options.get(id=option_id)
                        user_answer.selected_options.add(option)
                    except AnswerOption.DoesNotExist:
                        pass
                user_answer.save()

            elif question.question_type == Question.TEXT:
                # 文字填答的答案存在selected_options不合適，需額外欄位
                # 建議新增一個TextAnswer欄位，這裡先示範用UserAnswer的selected_options不存文字
                # 可以改成擴充UserAnswer，新增 text_answer = models.TextField(null=True, blank=True)
                text_answer = request.POST.get(field_name, '').strip()
                # 目前 UserAnswer 沒文字欄位，若要存文字，需改model（下方我會示範）
                # 這裡暫時跳過存文字
                # 可改成：
                # user_answer.text_answer = text_answer
                # user_answer.save()
                # 若沒擴充，請先忽略文字存儲
                # 如果要存文字，請參考下方的 model 及 view 修改示範
                pass

        # 儲存完跳轉或顯示成功訊息
        return redirect('agent:questionnaire_list')  # 你要自己新增一個謝謝頁面或跳轉回首頁

    # 載入使用者先前填寫答案
    user_answers = UserAnswer.objects.filter(user=user, question__in=questions).prefetch_related('selected_options')

    # ➤ 建立 question.id → set(option.id) 的映射
    answer_map = {
        answer.question.id: set(opt.id for opt in answer.selected_options.all())
        for answer in user_answers
    }

    # ➤ 將每個問題包成 dict，加上已選項目（selected_option_ids）
    questions_with_answers = []
    for q in questions:
        selected_ids = answer_map.get(q.id, set())
        questions_with_answers.append({
            'question': q,
            'selected_ids': selected_ids,
        })

    return render(request, 'questionnaire_detail.html', {
        'questionnaire': questionnaire,
        'questions_with_answers': questions_with_answers,
    })


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Questionnaire, UserQuestionnaireRecord, UserAnswer

@login_required
def questionnaire_list(request):
    user = request.user
    questionnaires = Questionnaire.objects.all()

    data = []
    for q in questionnaires:
        # 取得該問卷填寫紀錄 (可能沒有)
        record = UserQuestionnaireRecord.objects.filter(user=user, questionnaire=q).first()

        # 該問卷的題目
        questions = q.questions.all()
        total_questions = questions.count()

        # 使用者回答該問卷中的多少題
        answered_questions = UserAnswer.objects.filter(user=user, question__in=questions).exclude(selected_options=None).count()


        
        print(total_questions,answered_questions)
        if total_questions > 0:
            progress = int(answered_questions / total_questions * 100)
        else:
            progress = 0

        # 填寫狀況字串
        if progress == 0:
            status = "未填寫"
        elif progress == 100:
            status = "已填寫"
        else:
            status = f"填寫中 {progress}%"

        data.append({
            'questionnaire': q,
            'last_completed': record.completed_at if record else None,
            'status': status,
            'progress': progress,
        })

    return render(request, 'questionnaire_list.html', {
        'data': data,
    })


def get_user_answer_hash(user_id, questionnaire_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT q.content, ao.content
            FROM agent_useranswer ua
            JOIN agent_question q ON ua.question_id = q.id
            JOIN agent_useranswer_selected_options uso ON uso.useranswer_id = ua.id
            JOIN agent_answeroption ao ON uso.answeroption_id = ao.id
            WHERE ua.user_id = %s
                       AND q.questionnaire_id = %s
            ORDER BY q.id
        """, [user_id, questionnaire_id])
        rows = cursor.fetchall()

    combined = "|".join([f"{q}-{a}" for q, a in rows])
    return hashlib.sha256(combined.encode("utf-8")).hexdigest(), rows


def analyze_user_responses(user, questionnaire, api):
    

    # 計算目前填答 hash
    answer_hash, qa_pairs = get_user_answer_hash(user.id, questionnaire.id)
    print(questionnaire)

    

    # 取得紀錄（若不存在就建立）
    record, _ = UserQuestionnaireRecord.objects.get_or_create(
        user=user,
        questionnaire=questionnaire,
    )

    # 如果 hash 相同，代表沒改動過 → 直接回傳之前的結果
    if record.last_submitted_hash == answer_hash and record.gpt_analysis_result:
        return record.gpt_analysis_result

    # 產生 prompt
    prompt_lines = [f"Q: {q}\nA: {a}" for q, a in qa_pairs]
    print(prompt_lines)
    prompt = "以下是使用者的問卷回答進行分析，最後做個總結：\n\n" + "\n\n".join(prompt_lines)

    # 呼叫 v36 API
    try:
        url = 'https://free.v36.cm/v1/chat/completions'
        headers = {
            'Authorization': f'Bearer {api}',  # ← 這裡原本是錯的 api，已修正
            'Content-Type': 'application/json',
        }
        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        content = result['choices'][0]['message']['content']

        # 儲存結果
        record.gpt_analysis_result = content
        record.last_submitted_hash = answer_hash
        record.completed_at = timezone.now()
        record.save()

        return content
    except Exception as e:
        return f"分析失敗：{e}"
    
def get_total_analysis():
    records = UserQuestionnaireRecord.objects.filter(
        gpt_analysis_result__isnull=False
    ).select_related('questionnaire', 'user')

    analysis_blocks = []
    for record in records:
        title = record.questionnaire.title
        username = record.user.username
        analysis = record.gpt_analysis_result
        block = f"【問卷】{title}（使用者：{username}）\n{analysis}"
        analysis_blocks.append(block)

    prompt = (
        "以下是多份問卷的 GPT 分析結果，請根據這些內容進行第二層的彙總分析，列出整體觀察與建議：\n\n"
        + "\n\n".join(analysis_blocks)
    )

    url = 'https://free.v36.cm/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {api}',  # 從 settings 或 config 獲取
        'Content-Type': 'application/json',
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        content = result['choices'][0]['message']['content']
    except Exception as e:
        content = f"總分析時發生錯誤：{str(e)}"

    return content

def analyze_all_questionnaires(request):
    result = get_total_analysis()
    return render(request, "analysis_result.html", {
        "analysis": result
    })
    
@login_required
def analyze_view(request, questionnaire_id):
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)
    user = request.user
    print(f"[DEBUG] user = {user} (type={type(user)}) {questionnaire}")
    api_key = api  # 從 settings 抓你的 GPT key

    result = analyze_user_responses(user, questionnaire, api_key)

    return render(request, "analysis_result.html", {"analysis": result,})