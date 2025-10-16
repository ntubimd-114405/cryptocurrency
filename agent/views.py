from django.shortcuts import render

# agent/views.py
import requests
import hashlib
import pandas as pd
import json
import ta

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from dotenv import load_dotenv
from datetime import datetime, timedelta
import os
from pathlib import Path
from django.db import connection
from django.conf import settings
from main.models import CoinHistory, Coin
from decimal import Decimal

env_path = Path(__file__).resolve().parents[2] / '.env'

# 加載 .env 檔案
load_dotenv(dotenv_path=env_path)

api = os.getenv('OPENAI_API_KEY')

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
        'Authorization': f'Bearer {api}',
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

# 1. 問卷填寫與進度追蹤-----------
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Questionnaire, UserQuestionnaireRecord, UserAnswer

@login_required
def questionnaire_list(request):
    user = request.user
    questionnaires = Questionnaire.objects.all()

    # ---------- 初始化累加變數 ----------
    data = []
    total_all_questions = 0
    total_all_answered = 0

    for q in questionnaires:
        # 取得該問卷填寫紀錄 (可能沒有)
        record = UserQuestionnaireRecord.objects.filter(user=user, questionnaire=q).first()

        # 該問卷的題目
        questions = q.questions.all()
        total_questions = questions.count()

        # 使用者回答該問卷中的多少題
        answered_questions = UserAnswer.objects.filter(user=user, question__in=questions).exclude(selected_options=None).count()

        # 累計所有問卷題目與已回答題目數
        total_all_questions += total_questions
        total_all_answered += answered_questions

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
            'description': q.description,
            'last_completed': record.completed_at if record else None,
            'status': status,
            'progress': progress,
        })


    # ---------- 計算整體完成比例 ----------
    overall_progress = int(total_all_answered / total_all_questions * 100) if total_all_questions > 0 else 0
    overall_remaining = 100 - overall_progress

    user_profile = request.user.profile  # 取得使用者的 Profile
    know = not user_profile.has_seen_know_modal  # 只在未看過時顯示

    # 當使用者按下「我已了解」
    if request.method == 'POST' and request.POST.get('know_confirm') == '1':
        user_profile.has_seen_know_modal = True
        user_profile.save()
        return JsonResponse({'status': 'ok'})

    return render(request, 'questionnaire_list.html', {
        'data': data,
        'overall_progress': overall_progress,
        'overall_remaining': overall_remaining,
        'know': know,
    })
# -----------1. 問卷填寫與進度追蹤
# 重新填問卷
from django.views.decorators.http import require_POST

@login_required
@require_POST
def reset_questionnaire_answers(request, questionnaire_id):
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)

    # 1. 找出問卷下所有題目
    questions = questionnaire.questions.all()

    # 2. 刪除該使用者對這些題目的所有答案
    UserAnswer.objects.filter(user=request.user, question__in=questions).delete()

    # 3. 刪除填寫紀錄
    UserQuestionnaireRecord.objects.filter(user=request.user, questionnaire=questionnaire).delete()

    # 4. 重新導向到問卷填寫頁面
    return redirect('agent:questionnaire_detail', questionnaire_id=questionnaire.id)

#  4. 所有問卷的 AI 總分析----------- 
def get_total_analysis(user):

    records = UserQuestionnaireRecord.objects.filter(
        user=user,
        completed_at__isnull=False
    ).select_related('questionnaire')
        
    analysis_blocks = []
    for record in records:
        questionnaire_title = record.questionnaire.title

        answers = UserAnswer.objects.filter(
            user=user,
            question__questionnaire=record.questionnaire
        ).select_related('question').prefetch_related('selected_options')

        answer_texts = []
        for ans in answers:
            q_content = ans.question.content
            if ans.selected_options.exists():
                selected = "、".join([opt.content for opt in ans.selected_options.all()])
                answer_texts.append(f"題目: {q_content}\n回答: {selected}")
            else:
                answer_texts.append(f"題目: {q_content}\n回答: (未填)")

        user_block = f"問卷名稱: {questionnaire_title}\n" + "\n".join(answer_texts)
        analysis_blocks.append(user_block)

    prompt = (
        "以下是使用者填寫的投資相關問卷內容，請僅根據填答進行簡短分析，請使用繁體中文回答：\n\n"
        + "\n\n".join(analysis_blocks)
    )


    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {api}',
        'Content-Type': 'application/json',
    }
    data = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}]}

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
    except Exception as e:
        content = f"總分析時發生錯誤：{str(e)}"

    return content
#  ----------- 4. 所有問卷的 AI 總分析

# 2. 風險屬性分析與資產配置建議-----------
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import UserAnswer, Questionnaire
from main.models import Coin, CoinCategory, CoinCategoryRelation,BitcoinPrice
from django.db.models import Max
import random

RISK_QUESTIONNAIRE_IDS = [2, 3, 4, 9]

@login_required
def analysis_result_view(request):
    user = request.user

    # 取得全部分析結果（原 analyze_all_questionnaires）
    total_analysis = get_total_analysis(user)

    # 取得使用者的問卷風險分析
    user_answers = UserAnswer.objects.filter(
        user=user,
    ).prefetch_related("selected_options")

    total_score = 0
    answer_count = 0

    # 核心題目分數
    core_scores = {
        "score_investment_exp": 0, 
        "score_risk_pref": 0,
        "score_investment_goal": 0,
        "score_psychology": 0,
        "score_q7": 0,
    }
    core_counts = {k: 0 for k in core_scores}

    
    # 累計分數
    for ans in user_answers:
        for option in ans.selected_options.all():

            q_order = ans.question.questionnaire.id
            if q_order in RISK_QUESTIONNAIRE_IDS:
                total_score += option.score

                answer_count += 1        
            if q_order == 2:
                core_scores["score_investment_exp"] += option.score
                core_counts["score_investment_exp"] += 1
            elif q_order == 3:
                core_scores["score_risk_pref"] += option.score
                core_counts["score_risk_pref"] += 1
            elif q_order == 4:
                core_scores["score_investment_goal"] += option.score
                core_counts["score_investment_goal"] += 1
            elif q_order == 7:
                core_scores["score_q7"] += option.score
                core_counts["score_q7"] += 1
            elif q_order == 9:
                core_scores["score_psychology"] += option.score
                core_counts["score_psychology"] += 1

    # 分數計算
    if answer_count == 0:
        risk_type = "無法評估"
        suggestion = "請至少填寫第 1~9 題任一題，才能分析風險屬性。"
        average = None
        allocation = {}
        recommended_coins = {}
        core_scores_avg = {k: None for k in core_scores}
    else:
        average = total_score / answer_count

        core_scores_avg = {
            k: round(core_scores[k] / core_counts[k] * 20, 2) if core_counts[k] > 0 else 0
            for k in core_scores
        }

        # allocation 與風險屬性判斷
        ratio = min(max(average / 5, 0), 1)
        allocation = {
            "穩定幣": 0.6 * (1 - ratio),
            "主流幣": 0.3,
            "成長幣": 0.1 + 0.3 * ratio,
            "迷因幣": 0.0 + 0.2 * ratio,
        }
        total = sum(allocation.values())
        allocation = {k: round(v/total, 2) for k, v in allocation.items()}

        if average <= 2.5:
            risk_type = "保守型"
        elif average <= 4:
            risk_type = "穩健型"
        else:
            risk_type = "積極型"

        recommended_coins = {}

        for category_name, ratio_value in allocation.items():
            try:
                category = CoinCategory.objects.get(name=category_name)
                # 取得屬於該類別的所有幣種
                coins_in_category = Coin.objects.filter(coincategoryrelation__category=category)

                if coins_in_category.exists():
                    # 取得所有幣種的市值資料，並根據市值排序
                    # 使用 GROUP BY 和 MAX() 來確保每個 Coin 只取一個最大市值資料
                    coins_with_market_cap = BitcoinPrice.objects.filter(coin__in=coins_in_category) \
                        .values('coin') \
                        .annotate(max_market_cap=Max('market_cap')) \
                        .order_by('-max_market_cap')

                    # 取出市值最高的前三個幣種
                    top_coins = []
                    for entry in coins_with_market_cap[:3]:
                        coin = Coin.objects.get(id=entry['coin'])
                        top_coins.append(coin)

                    # 組織推薦幣種的名稱
                    recommended_coins[category_name] = [coin for coin in top_coins]
                else:
                    recommended_coins[category_name] = []

            except CoinCategory.DoesNotExist:
                recommended_coins[category_name] = []

        suggestion = "、".join([f"{int(v*100)}% {k}" for k, v in allocation.items() if v > 0])

    # allocation_data 保留
    allocation_data = [
        int(allocation.get("穩定幣", 0) * 100),
        int(allocation.get("主流幣", 0) * 100),
        int(allocation.get("成長幣", 0) * 100),
        int(allocation.get("迷因幣", 0) * 100),
    ]

   # ---------- 總進度計算 ----------
    progress_data = []
    total_questions_all = 0
    answered_questions_all = 0

    # 取得所有問卷
    questionnaires = Questionnaire.objects.all()

    for q in questionnaires:
        questions = q.questions.all()
        total_questions = questions.count()
        answered_questions = UserAnswer.objects.filter(
            user=user,
            question__in=questions
        ).exclude(selected_options=None).count()

        # 累加全部問卷的總題數與已答題數
        total_questions_all += total_questions
        answered_questions_all += answered_questions

        # 總進度資料 (方便前端直接使用)
        progress_data.append({
            "name": f"問卷{q.id}",           # 問卷名稱
            "answered": answered_questions,  # 已完成題數
            "unanswered": total_questions - answered_questions  # 未完成題數
        })

    # 整體完成度
    overall_progress2 = {
        "answered": answered_questions_all,
        "total": total_questions_all,
        "percent": int(answered_questions_all / total_questions_all * 100) if total_questions_all > 0 else 0
    }


    return render(request, "analysis_all_result.html", {
        "overall_progress2": overall_progress2,
        "analysis": total_analysis,
        "average_score": round(average, 2) if average is not None else None,
        "risk_type": risk_type,
        "suggestion": suggestion,
        "recommended_coins": recommended_coins,
        "allocation_data": allocation_data,
        "allocation": allocation,
        "core_scores_avg": core_scores_avg, #核心題目分數
        "progress_data": progress_data,
    })


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)
    
# agent/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from agent.knowledge.knowledge_agent import ask_knowledge_agent
import json

# 前端頁面
def chat_page(request):
    return render(request, "chat.html")

# 接收 POST 問題並回覆答案
@csrf_exempt
def knowledge_chat_view(request):
    if request.method == "POST":
        data = json.loads(request.body)
        question = data.get("question", "")
        if not question.strip():
            return JsonResponse({"answer": "❗請輸入有效的問題"}, status=400)
        answer = ask_knowledge_agent(question)
        return JsonResponse({"answer": answer})
    return JsonResponse({"error": "只接受 POST 請求"}, status=405)