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
from django.utils.dateparse import parse_datetime

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

def invest_view(request):
    # 定義你要展示的策略清單 (對應你後端代碼中的 strategy_name)
    strategies = [
        {
            "id": "EMA_CROSS",
            "title": "EMA Cross Strategy",
            "description": "短期 EMA10 與中期 EMA20 黃金交叉/死亡交叉策略，適用於趨勢追蹤。",
            "tags": ["Trend", "Moving Average"],
            "color": "#2962FF",
            "url_name": "agent:ema_detail"
        },
        {
            "id": "RSI_REVERSION",
            "title": "RSI Mean Reversion",
            "description": "利用 RSI 超買(>70)與超賣(<30)進行反向操作，適用於震盪盤整市場。",
            "tags": ["Oscillator", "Reversal"],
            "color": "#E91E63",
            "url_name": "agent:rsi_detail"
        },
        {
            "id": "MACD_CROSS",
            "title": "MACD Momentum",
            "description": "結合趨勢跟隨與動能分析的經典指標，利用快慢線交叉識別買賣訊號，並透過柱狀圖變化判斷市場多空力道強弱。",
            "tags": ["Momentum", "MACD"],
            "color": "#00BCD4",
            "url_name": "agent:macd_detail"
        },
        # {
        #     "id": "BBANDS_REVERSION", 
        #     "title": "Bollinger Bands Strategy",
        #     "description": "布林通道突破與回歸策略，捕捉波動率變化。",
        #     "tags": ["Volatility", "Bands"],
        #     "color": "#FF9800"
        # },
        
        # 你可以繼續添加你的其他策略...
    ]

    context = {
        "strategies": strategies,
        # 預設顯示的幣種 ID，你可以根據需要傳入
        "default_coin_id": 1 
    }
    return render(request, 'invest.html', context)

def get_ai_strategy_analysis(short_ma=20, long_ma=50):
    print("--- [Step 1] 開始呼叫 OpenAI API ---")
    """
    使用 ChatGPT API 生成 EMA 策略分析與大師觀點
    """
    
    # 1. 構建 Prompt：這是核心，決定了 AI 輸出的品質
    # 我們要求 AI 扮演「資深量化分析師」，並明確要求包含「策略原理」與「大師哲學」
    prompt = f"""
    你是一位資深的加密貨幣量化交易分析師。請針對「EMA 雙均線交叉策略」生成一份專業的分析報告。
    
    【策略參數】
    - 短期均線：EMA {short_ma}
    - 長期均線：EMA {long_ma}
    - 交易邏輯：短線上穿長線為買入（黃金交叉），短線下穿長線為賣出（死亡交叉）。

    【請回答以下兩點，並使用繁體中文】：
    
    1. **策略深度解析**：
       請用簡練但專業的語言解釋此策略的核心邏輯。請不要只說「交叉就買」，請解釋這背後代表的「趨勢動能」與「市場平均成本」的變化。請提及 EMA 相較於 SMA (簡單移動平均) 對近期價格更敏感的優勢。

    2. **投資大師哲學連結**：
       請舉例說明哪位著名的傳奇交易員或投資大師（例如：Stan Weinstein 史丹·温斯坦、Paul Tudor Jones 保羅·都鐸·瓊斯、或是 Ed Seykota 艾德·斯科塔）的交易哲學與「趨勢跟隨 (Trend Following)」或「移動平均線」有異曲同工之妙？
       請引用他們的經典名言或核心概念（例如「階段分析」或「200日均線法則」），並解釋為何這個 EMA 策略符合該大師的邏輯。

    【格式要求】：
    - 請使用 HTML 標籤進行排版（使用 <h3>, <p>, <ul>, <li>, <strong>）。
    - 語氣要客觀、理性、具備教育意義。
    - 總字數控制在 400 字以內。
    """

    # 2. 設定 API 參數
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {api}',
        'Content-Type': 'application/json',
    }
    
    # 3. 呼叫模型 (使用 gpt-4o-mini 以節省成本且速度快)
    data = {
        "model": "gpt-4o-mini", 
        "messages": [
            {"role": "system", "content": "你是一位專業的金融科技與量化交易專家，擅長用淺顯易懂的方式解釋複雜的交易策略。"},
            {"role": "user", "content": prompt}
        ],
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"--- [Step 2] API 回應狀態碼: {response.status_code} ---")
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        return content
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        # 如果失敗，回傳一個備用的靜態描述，避免頁面壞掉
        return """
        <h3>策略分析暫時無法載入</h3>
        <p>目前無法連接至 AI 分析伺服器，請稍後再試。EMA 策略是一種經典的趨勢跟隨系統，利用短期與長期均線的交叉來捕捉市場的主要波段。</p>
        """

def ema_detail(request):
    
    coin_id = 1 
    
    # 設定預設時間範圍 (例如：過去 30 天)
    end = timezone.now()
    start = end - timedelta(days=1)

    # 如果網址有帶參數 (?coin_id=2)，也可以優先使用
    if request.GET.get('coin_id'):
        try:
            coin_id = int(request.GET.get('coin_id'))
        except ValueError:
            pass

    qs = (
        CoinHistory.objects.filter(
            coin_id=coin_id,
            date__gte=start,
            date__lte=end
        )
        .order_by('date')
        # 這裡可以決定要不要限制筆數，例如 [:1500]
    )
    
    records = list(qs)
    
    # 轉成列表字典 (這是你要的 data 格式)
    raw_data = [
        {
            "date": int(item.date.timestamp() * 1000),
            "open": float(item.open_price),
            "high": float(item.high_price),
            "low": float(item.low_price),
            "close": float(item.close_price),
            "volume": float(item.volume),
        }
        for item in records
    ]

    ai_analysis_html = get_ai_strategy_analysis(short_ma=20, long_ma=50)

    context = {
        # 為了讓 JavaScript 能讀取，這裡要用 json.dumps 轉成字串
        "chart_data": json.dumps(raw_data),
        "coin_id": coin_id,
        'ai_analysis': ai_analysis_html  # 傳遞給 Template
    }
    
    return render(request, 'ema_detail.html', context)

def get_ai_strategy_rsi_analysis(period=14, overbought=70, oversold=30):
    print("--- [Step 1] 開始呼叫 OpenAI API (RSI 策略) ---")
    """
    使用 ChatGPT API 生成 RSI 策略分析與大師觀點
    """
    
    # 1. 構建 Prompt：針對 RSI 策略進行客製化
    # 我們要求 AI 解釋「動能指標」與「均值回歸」的概念
    prompt = f"""
    你是一位資深的加密貨幣量化交易分析師。請針對「RSI 相對強弱指標策略 (Relative Strength Index)」生成一份專業的分析報告。
    
    【策略參數】
    - RSI 計算週期：{period}
    - 超買閾值 (Overbought)：{overbought}
    - 超賣閾值 (Oversold)：{oversold}
    - 交易邏輯：當 RSI 低於 {oversold} 時視為超賣（潛在買點）；當 RSI 高於 {overbought} 時視為超買（潛在賣點）。

    【請回答以下兩點，並使用繁體中文】：
    
    1. **策略深度解析**：
       請用簡練但專業的語言解釋 RSI 作為「動能震盪指標」的核心邏輯。
       請解釋「超買」代表買盤力道過熱可能有回調風險，而「超賣」代表非理性拋售可能有反彈機會。請提及此策略捕捉「均值回歸 (Mean Reversion)」行情的優勢。

    2. **投資大師哲學連結**：
       請連結到技術分析大師 **J. Welles Wilder Jr. (RSI 的發明者)** 的交易哲學。
       或是引用其他擅長「逆勢交易 (Contrarian Trading)」的大師觀點（如巴菲特的「別人恐懼我貪婪」概念在技術面上的體現）。
       請解釋為何 RSI 指標能幫助交易者克服追高殺低的人性弱點。

    【格式要求】：
    - 請使用 HTML 標籤進行排版（使用 <h3>, <p>, <ul>, <li>, <strong>）。
    - 語氣要客觀、理性、具備教育意義。
    - 總字數控制在 400 字以內。
    """

    # 2. 設定 API 參數
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {api}', # 確保這裡傳入正確的 API Key 變數
        'Content-Type': 'application/json',
    }
    
    # 3. 呼叫模型
    data = {
        "model": "gpt-4o-mini", 
        "messages": [
            {"role": "system", "content": "你是一位專業的金融科技與量化交易專家，擅長用淺顯易懂的方式解釋震盪指標與逆勢策略。"},
            {"role": "user", "content": prompt}
        ],
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"--- [Step 2] API 回應狀態碼: {response.status_code} ---")
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        return content
    
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        # 4. 錯誤處理：回傳 RSI 專用的備用靜態描述
        return f"""
        <h3>RSI 策略分析暫時無法載入</h3>
        <p>目前無法連接至 AI 分析伺服器。<strong>RSI (相對強弱指標)</strong> 是一種動能震盪指標，主要用於評估價格變動的速度與變化。</p>
        <ul>
            <li><strong>超買區 (> {overbought})</strong>：暗示行情可能過熱，隨時有回調風險。</li>
            <li><strong>超賣區 (< {oversold})</strong>：暗示行情可能過度拋售，存在反彈機會。</li>
        </ul>
        """

def rsi_detail(request):
    
    coin_id = 2 
    
    # 設定預設時間範圍 (例如：過去 30 天)
    end = timezone.now()
    start = end - timedelta(days=1)

    # 如果網址有帶參數 (?coin_id=2)，也可以優先使用
    if request.GET.get('coin_id'):
        try:
            coin_id = int(request.GET.get('coin_id'))
        except ValueError:
            pass

    qs = (
        CoinHistory.objects.filter(
            coin_id=coin_id,
            date__gte=start,
            date__lte=end
        )
        .order_by('date')
        # 這裡可以決定要不要限制筆數，例如 [:1500]
    )
    
    records = list(qs)
    
    # 轉成列表字典 (這是你要的 data 格式)
    raw_data = [
        {
            "date": int(item.date.timestamp() * 1000),
            "open": float(item.open_price),
            "high": float(item.high_price),
            "low": float(item.low_price),
            "close": float(item.close_price),
            "volume": float(item.volume),
        }
        for item in records
    ]

    ai_analysis_html = get_ai_strategy_rsi_analysis(period=14, overbought=70, oversold=30)

    context = {
        # 為了讓 JavaScript 能讀取，這裡要用 json.dumps 轉成字串
        "chart_data": json.dumps(raw_data),
        "coin_id": coin_id,
        'ai_analysis': ai_analysis_html  # 傳遞給 Template
    }
    
    return render(request, 'rsi_detail.html', context)

def get_ai_strategy_macd_analysis(fast_period=12, slow_period=26, signal_period=9):
    print("--- [Step 1] 開始呼叫 OpenAI API (MACD 策略) ---")
    """
    使用 ChatGPT API 生成 MACD 策略分析與大師觀點
    """
    
    # 1. 構建 Prompt：針對 MACD 策略進行客製化
    # MACD 是趨勢與動能的結合，Prompt 重點在於「趨勢確認」與「動能變化」
    prompt = f"""
    你是一位資深的加密貨幣量化交易分析師。請針對「MACD 指數平滑異同移動平均線策略 (Moving Average Convergence Divergence)」生成一份專業的分析報告。
    
    【策略參數】
    - 快線 (Fast EMA)：{fast_period}
    - 慢線 (Slow EMA)：{slow_period}
    - 訊號線 (Signal EMA)：{signal_period}
    - 交易邏輯：當 DIF (快慢線差) 向上突破 DEM (訊號線) 為買入訊號（黃金交叉）；當 DIF 向下跌破 DEM 為賣出訊號（死亡交叉）。

    【請回答以下兩點，並使用繁體中文】：
    
    1. **策略深度解析**：
       請用簡練但專業的語言解釋 MACD 如何同時捕捉「趨勢方向」與「動能強弱」。
       請解釋「柱狀圖 (Histogram)」擴大與縮小代表的市場心理變化（例如：柱狀圖由負轉正代表空頭力道衰竭，多頭動能轉強）。

    2. **投資大師哲學連結**：
       請連結到 MACD 的發明者 **Gerald Appel (傑拉德·阿佩爾)** 的交易哲學。
       或是引用 **Alexander Elder (亞歷山大·艾爾德)** 在《操作生涯不是夢》中提到的「三重濾網系統」，解釋 MACD 在其中扮演的角色（通常用於判斷動能）。
       請解釋為何 MACD 比單純的移動平均線更能過濾雜訊。

    【格式要求】：
    - 請使用 HTML 標籤進行排版（使用 <h3>, <p>, <ul>, <li>, <strong>）。
    - 語氣要客觀、理性、具備教育意義。
    - 總字數控制在 400 字以內。
    """

    # 2. 設定 API 參數
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {api}', # 確保這裡傳入正確的 API Key
        'Content-Type': 'application/json',
    }
    
    # 3. 呼叫模型
    data = {
        "model": "gpt-4o-mini", 
        "messages": [
            {"role": "system", "content": "你是一位專業的金融科技與量化交易專家，擅長用淺顯易懂的方式解釋趨勢跟隨與動能策略。"},
            {"role": "user", "content": prompt}
        ],
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"--- [Step 2] API 回應狀態碼: {response.status_code} ---")
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        return content
    
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        # 4. 錯誤處理：回傳 MACD 專用的備用靜態描述
        return f"""
        <h3>MACD 策略分析暫時無法載入</h3>
        <p>目前無法連接至 AI 分析伺服器。<strong>MACD (指數平滑異同移動平均線)</strong> 是一種結合趨勢與動能的經典指標。</p>
        <ul>
            <li><strong>黃金交叉 (買入)</strong>：當 DIF 快線由下往上穿越 MACD 訊號線，且柱狀圖由負轉正。</li>
            <li><strong>死亡交叉 (賣出)</strong>：當 DIF 快線由上往下穿越 MACD 訊號線，且柱狀圖由正轉負。</li>
        </ul>
        """

def macd_detail(request):
    
    coin_id = 4 
    
    # 設定預設時間範圍 (例如：過去 30 天)
    end = timezone.now()
    start = end - timedelta(days=1)

    # 如果網址有帶參數 (?coin_id=2)，也可以優先使用
    if request.GET.get('coin_id'):
        try:
            coin_id = int(request.GET.get('coin_id'))
        except ValueError:
            pass

    qs = (
        CoinHistory.objects.filter(
            coin_id=coin_id,
            date__gte=start,
            date__lte=end
        )
        .order_by('date')
        # 這裡可以決定要不要限制筆數，例如 [:1500]
    )
    
    records = list(qs)
    
    # 轉成列表字典 (這是你要的 data 格式)
    raw_data = [
        {
            "date": int(item.date.timestamp() * 1000),
            "open": float(item.open_price),
            "high": float(item.high_price),
            "low": float(item.low_price),
            "close": float(item.close_price),
            "volume": float(item.volume),
        }
        for item in records
    ]

    ai_analysis_html = get_ai_strategy_macd_analysis(fast_period=12, slow_period=26, signal_period=9)

    context = {
        # 為了讓 JavaScript 能讀取，這裡要用 json.dumps 轉成字串
        "chart_data": json.dumps(raw_data),
        "coin_id": coin_id,
        'ai_analysis': ai_analysis_html  # 傳遞給 Template
    }
    
    return render(request, 'macd_detail.html', context)