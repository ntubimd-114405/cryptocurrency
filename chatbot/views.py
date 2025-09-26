import os
import re
import json
import requests
from decimal import Decimal, ROUND_HALF_UP, getcontext
from dotenv import load_dotenv
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from main.models import Coin  # 從 main app import Coin

# ✅ 載入 .env
load_dotenv()
API_KEY = os.getenv("API_KEY")  # 你的 GPT API Key
CMC_API_KEY = os.getenv("coinmarketcap_api")
API_URL = 'https://free.v36.cm/v1/chat/completions'


# ✅ 前端頁面
def chatbot_page(request):
    return render(request, 'chatbot/chat.html')


# ✅ 格式化加密貨幣價格
def format_crypto_price(price):
    """
    將加密貨幣價格格式化：
    - price >= 1 顯示兩位小數
    - price < 1 顯示從第一個非零數字開始的三位有效數字，四捨五入
    """
    if price >= 1:
        return f"${price:.2f}"
    else:
        getcontext().prec = 10
        d = Decimal(str(price))
        exponent = d.adjusted()
        digits_needed = 3
        rounded = d.quantize(Decimal('1e{}'.format(exponent - digits_needed + 1)), rounding=ROUND_HALF_UP)
        return f"${rounded.normalize()}"


# ✅ 從輸入文字解析幣種 abbreviation（Regex + DB 查詢）
def resolve_symbols_from_db(text):
    text_lower = text.lower().strip()
    results = []
    words = re.findall(r"[a-zA-Z0-9]+", text_lower)

    for word in words:
        qs = Coin.objects.filter(abbreviation__iexact=word)
        if qs.exists():
            results.append(qs.first().abbreviation.upper())
            continue
        qs = Coin.objects.filter(coinname__icontains=word)
        if qs.exists():
            results.append(qs.first().abbreviation.upper())

    return list(set(results))


def extract_symbols(text):
    regex_symbols = re.findall(r'\b[A-Z]{2,10}\b', text)
    db_symbols = resolve_symbols_from_db(text)
    return list(set(regex_symbols + db_symbols))


# ✅ 從 CoinMarketCap 查即時價格與漲跌
def get_crypto_prices(symbols):
    if not symbols:
        return {}

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
            return {}

        result = {}
        for sym in symbols:
            coin = data["data"].get(sym.upper())
            if not coin:
                continue
            price = coin["quote"]["USD"]["price"]
            change = coin["quote"]["USD"]["percent_change_24h"]
            result[sym.upper()] = {
                "price": price,
                "change": change
            }
        return result
    except Exception:
        return {}


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
                            "只能用英文或者繁體中文。\n"
                            "你是加密貨幣專家 AI，只允許回答與虛擬貨幣、區塊鏈、代幣、DeFi、NFT、市場趨勢有關的問題。\n"
                            "若使用者的問題與主題無關，請回覆：「我只能協助回答加密貨幣相關的問題喔」。\n"
                            "⚠️ 特別規則：\n"
                            "- 幣種價格只能來自『📊 補充幣價資訊』，不要自己生成或假設數字。\n"
                            "- 若補充資料中沒有該幣種，請回答「目前暫時查不到該幣種的價格」。\n"
                            "風格要求：\n"
                            "- 回答簡短精要\n"
                            "- 不要寫長篇大論\n"
                        )
                    }
                ]

            chat_history = request.session[session_key]

            # ✅ 偵測幣種（Regex + DB）
            mentioned_symbols = extract_symbols(user_prompt)
            price_data = get_crypto_prices(mentioned_symbols)

            # ✅ 生成 price_info_text
            price_info_text = ""
            if price_data:
                lines = []
                for sym, info in price_data.items():
                    formatted_price = format_crypto_price(info['price'])
                    change = info['change']
                    lines.append(f"💰 {sym}: {formatted_price}（24h 漲跌 {change:+.2f}%）")
                price_info_text = "\n".join(lines)
                user_prompt += f"\n\n📊 補充幣價資訊：\n{price_info_text}"

            chat_history.append({"role": "user", "content": user_prompt})

            # ✅ 發送給 GPT
            headers = {
                'Authorization': f'Bearer {API_KEY}',
                'Content-Type': 'application/json',
            }
            data = {
                "model": "gpt-3.5-turbo",
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

            # ✅ 回傳 GPT 回答 + 真實價格數據
            return JsonResponse({
                'reply': reply,
                'prices': price_data
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    else:
        return JsonResponse({'error': '只支援 POST 請求'}, status=405)


# ---- 顯示 WebChat 頁面 ----
def webchat_page(request):
    return render(request, 'chatbot/cai.html')