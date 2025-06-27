from django.shortcuts import render

# agent/views.py
import requests

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import UserProfile
from django.http import JsonResponse
from dotenv import load_dotenv
from datetime import datetime, timedelta
import os
from pathlib import Path

env_path = Path(__file__).resolve().parents[2] / '.env'

# 加載 .env 檔案
load_dotenv(dotenv_path=env_path)

api = os.getenv('OPEN_API')

@login_required
def user_questionnaire(request):
    if request.method == 'POST':
        risk_type = request.POST['risk_type']
        investment_goal = request.POST['investment_goal']
        total_budget = request.POST['total_budget']
        tolerance = request.POST['tolerance_per_coin']

        # ➤ 產生 GPT prompt
        user_prompt = f"""
        我是一位「{risk_type}」投資人，我的投資目標是「{investment_goal}」，
        我的總投資預算是 {total_budget} 元，對於單一幣種的最大容忍金額是 {tolerance} 元。
        請根據這些資訊，建議我一個加密貨幣的資產配置策略，並說明理由。
        """

        # ➤ 呼叫 GPT API
        url = 'https://free.v36.cm/v1/chat/completions'
        headers = {
            'Authorization': f'Bearer {api}',
            'Content-Type': 'application/json',
        }
        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "user", "content": user_prompt}
            ]
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            gpt_reply = response.json()['choices'][0]['message']['content']
        except Exception as e:
            gpt_reply = f"GPT API 發生錯誤：{str(e)}"

        # ➤ 存入資料庫
        profile, created = UserProfile.objects.update_or_create(
            user=request.user,
            defaults={
                'risk_type': risk_type,
                'investment_goal': investment_goal,
                'total_budget': total_budget,
                'tolerance_per_coin': tolerance,
            }
        )

        # ➤ 將 GPT 回應傳到前端顯示
        return render(request, 'asset_suggestion.html', {'gpt_reply': gpt_reply,'profile': profile})

    return render(request, 'questionnaire.html')



@login_required
def asset_suggestion(request):
    profile = UserProfile.objects.get(user=request.user)

    # 配置建議
    ALLOCATIONS = {
        '保守型': {'穩定幣': 60, '主流幣': 40},
        '中性型': {'主流幣': 50, 'DeFi幣': 30, '穩定幣': 20},
        '積極型': {'DeFi幣': 40, 'Meme幣': 30, '小幣': 30},
    }

    allocation = ALLOCATIONS.get(profile.risk_type, {})
    budget = float(profile.total_budget)
    suggestion = {k: round(budget * v / 100, 2) for k, v in allocation.items()}

    return render(request, 'asset_suggestion.html', {
        'profile': profile,
        'suggestion': suggestion,
    })

def call_free_chatgpt_api(request):
    # 從 GET 取得使用者輸入
    user_input = request.GET.get('prompt', 'Hello!')

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
            {"role": "user", "content": user_input}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return JsonResponse(result)
    
    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': str(e)}, status=500)