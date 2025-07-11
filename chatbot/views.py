import os
from dotenv import load_dotenv
import requests
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import json

# ✅ 載入 .env
load_dotenv()

API_KEY = os.getenv("API_KEY")
API_URL = 'https://free.v36.cm/v1/chat/completions'


# ✅ 前端頁面
def chatbot_page(request):
    return render(request, 'chatbot/chat.html')


# ✅ API
@csrf_exempt
def chat_api(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            user_prompt = body.get('message')
            user_id = body.get('user_id')
            clear = body.get('clear', False)

            if not user_id:
                return JsonResponse({'error': '請提供 user_id 參數'}, status=400)

            session_key = f'chat_history_{user_id}'

            # ✅ 清除記憶
            if clear:
                if session_key in request.session:
                    del request.session[session_key]
                return JsonResponse({'reply': '記憶已清除 🧹'})

            if not user_prompt:
                return JsonResponse({'error': '請提供 message 參數'}, status=400)

            # ✅ 初始記憶內容
            if session_key not in request.session:
                request.session[session_key] = [
                    {
                        "role": "system",
                        "content": (
                            "你是加密貨幣專家 AI，只允許回答與虛擬貨幣、區塊鏈、代幣、DeFi、NFT、市場趨勢等有關的問題。"
                            "若使用者的問題與主題無關（如天氣、感情、飲食、政治等），請回覆：「我只能協助回答加密貨幣相關的問題喔」。"
                        )
                    }
                ]

            chat_history = request.session[session_key]
            chat_history.append({"role": "user", "content": user_prompt})

            headers = {
                'Authorization': f'Bearer {API_KEY}',
                'Content-Type': 'application/json',
            }
            data = {
                "model": "gpt-4o-mini",
                "messages": chat_history
            }

            response = requests.post(API_URL, headers=headers, json=data)
            res_data = response.json()

            if response.status_code != 200:
                error_message = res_data.get('error') or res_data
                return JsonResponse({'error': str(error_message)}, status=500)

            reply = res_data['choices'][0]['message']['content']
            chat_history.append({"role": "assistant", "content": reply})
            request.session[session_key] = chat_history

            return JsonResponse({'reply': reply})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': '只支援 POST 請求'}, status=405)
