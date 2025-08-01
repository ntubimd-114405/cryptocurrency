import os
import re
import json
import requests
from dotenv import load_dotenv
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

# ✅ 載入 .env
load_dotenv()
API_KEY = os.getenv("API_KEY")  # 你的 GPT API Key
CMC_API_KEY = os.getenv("coinmarketcap_api")
API_URL = 'https://free.v36.cm/v1/chat/completions'

# ✅ 前端頁面
def chatbot_page(request):
    return render(request, 'chatbot/chat.html')

# ✅ 快取幣種 symbol -> id （可選）
symbol_to_id_cache = {}

# ✅ 擷取幣種 symbol（2~5碼英文大寫）
def extract_symbols(text):
    return list(set(re.findall(r'\b[A-Z]{2,5}\b', text)))

# ✅ 從 CoinMarketCap 查即時價格與漲跌
def get_crypto_prices(symbols):
    if not symbols:
        return ""

    try:
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        symbol_str = ','.join(symbols)
        headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': CMC_API_KEY,
        }
        params = {
            'symbol': symbol_str,
            'convert': 'USD'
        }
        res = requests.get(url, headers=headers, params=params, timeout=10)
        data = res.json()

        if res.status_code != 200 or "data" not in data:
            return ""

        result = []
        for sym in symbols:
            coin = data["data"].get(sym.upper())
            if not coin:
                continue
            price = coin["quote"]["USD"]["price"]
            change = coin["quote"]["USD"]["percent_change_24h"]
            result.append(f"💰 {sym.upper()}: ${price:.2f}（24h 漲跌 {change:+.2f}%）")

        return "\n".join(result)
    except Exception as e:
        return ""

# ✅ Chat API
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

            # ✅ 系統 prompt 初始化
            if session_key not in request.session:
                request.session[session_key] = [
                    {
                        "role": "system",
                        "content": (
                            "只能用英文或者繁體中文"
                            "你是加密貨幣專家 AI，只允許回答與虛擬貨幣、區塊鏈、代幣、DeFi、NFT、市場趨勢等有關的問題。"
                            "若使用者的問題與主題無關（如天氣、感情、飲食、政治等），請回覆：「我只能協助回答加密貨幣相關的問題喔」。"
                            "另外，如果使用者的問題涉及幣種的價格、走勢或行情，使用者訊息中可能會附加一段名為『📊 補充幣價資訊』的資料，"
                            "那是你可以信任的即時價格數據，請務必參考並根據這些數據提供準確的分析和建議。"
                            "風格要求：\n"
                            "- 回答務必簡短精要\n"
                            "- 不要寫太多段落或長篇敘述\n\n"
                        )
                    }
                ]

            chat_history = request.session[session_key]

            # ✅ 偵測幣種並補充幣價
            mentioned_symbols = extract_symbols(user_prompt)
            price_info = get_crypto_prices(mentioned_symbols)
            if price_info:
                user_prompt += f"\n\n📊 補充幣價資訊：\n{price_info}"

            chat_history.append({"role": "user", "content": user_prompt})

            # ✅ 發送給 GPT
            headers = {
                'Authorization': f'Bearer {API_KEY}',
                'Content-Type': 'application/json',
            }
            data = {
                "model": "gpt-3.5-turbo-0125",
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
