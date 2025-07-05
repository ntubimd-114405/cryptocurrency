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

            if not user_prompt:
                return JsonResponse({'error': '請提供 message 參數'}, status=400)

            headers = {
                'Authorization': f'Bearer {API_KEY}',
                'Content-Type': 'application/json',
            }
            data = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "user", "content": user_prompt}
                ]
            }

            response = requests.post(API_URL, headers=headers, json=data)
            res_data = response.json()

            if response.status_code != 200:
                error_message = res_data.get('error') or res_data
                return JsonResponse({'error': str(error_message)}, status=500)

            reply = res_data['choices'][0]['message']['content']

            return JsonResponse({'reply': reply})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': '只支援 POST 請求'}, status=405)
