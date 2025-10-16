from django.shortcuts import render, get_object_or_404,redirect
import requests
from django.http import JsonResponse,HttpResponseRedirect
from .models import BitcoinPrice,UserProfile,Coin,CoinHistory,User,FeedbackQuestion,FeedbackAnswer,PageTracker
from datetime import datetime, timedelta
from django.core.paginator import Paginator
# 登入頁面
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import UserProfileForm
from PIL import Image
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from io import BytesIO
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.utils.safestring import mark_safe
import plotly.graph_objects as go
from django.templatetags.static import static
from django.utils.timezone import now
import re
import pandas as pd
from decimal import Decimal
import ta
from pathlib import Path
from dotenv import load_dotenv

import os
import numpy as np

env_path = Path(__file__).resolve().parents[2] / '.env'

# 加載 .env 檔案
load_dotenv(dotenv_path=env_path)

api = os.getenv('OPEN_API')

def home(request):
    try:
        today = timezone.now().date()

        sign_in_record = None
        progress_percentage = 0

        if request.user.is_authenticated:
            user = request.user
            sign_in_record = SignIn.objects.filter(user=user).first()

            if sign_in_record:
                progress_days = sign_in_record.consecutive_sign_in_count % 7
                progress_percentage = int((progress_days / 7) * 100)

                if progress_days == 0 and sign_in_record.consecutive_sign_in_count > 0:
                    progress_percentage = 100

        # 資料查詢
        top_coins = BitcoinPrice.objects.all().order_by('id')[:5]
        increase_coins = BitcoinPrice.objects.all().order_by('-change_24h')[:5]
        decline_coins = BitcoinPrice.objects.all().order_by('change_24h')[:5]
        volume = BitcoinPrice.objects.all().order_by('-volume_24h')[:5]
        image_url = request.build_absolute_uri(static('images/crypto.png')) 
        
        return render(request, 'home.html', {
            'top_coins': top_coins,
            'increase_coins': increase_coins,
            'decline_coins': decline_coins,
            'volume': volume,
            'image_url': image_url,
            'sign_in_record': sign_in_record,
            'today': today,
            'progress_percentage': progress_percentage,
        })

    except Exception as e:
        print(f"錯誤: {e}")
        return render(request, 'home.html', {
            'error': '無法獲取資料，請稍後再試。'
        })


#註冊
from django.db import IntegrityError
def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')

        # 檢查用戶名是否已經存在
        if User.objects.filter(username=username).exists():
            messages.error(request, '這個用戶名已經被使用')
            return render(request, 'register.html')

        # 檢查郵箱是否已經註冊
        if User.objects.filter(email=email).exists():
            messages.error(request, '這個email已經被使用')
            return render(request, 'register.html')

        try:
            # 使用 create_user 方法創建用戶，自動加密密碼
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name
            )
            # 註冊成功後返回註冊頁面以顯示彈跳頁面
            messages.success(request, '您的帳戶已創建成功！請登入。')
            return render(request, 'register.html')

        except IntegrityError:
            messages.error(request, '用戶名或郵箱已存在，請選擇其他值')
            return render(request, 'register.html')
        except Exception as e:
            messages.error(request, f'創建用戶時發生錯誤：{e}')
            return render(request, 'register.html')

    return render(request, 'register.html')

    


# 登入頁面
def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')  # 登入成功後跳轉到首頁
        else:
            return render(request, 'login.html', {'error': '使用者名稱或密碼錯誤，請重新輸入一次'})
    return render(request, 'login.html')

# 登出功能
def logout_view(request):
    logout(request)
    return redirect('home')  # 登出後跳轉到登入頁

from django.db.models import F
from django.core.paginator import Paginator
from django.shortcuts import render

def format_crypto_price(value):
    """格式化虛擬貨幣價格，根據數值大小顯示適當的小數位數，並加上千分位符號"""
    try:
        value = float(value)
        if value == 0:
            return "0.00"
        elif value >= 1:
            # 大於等於 1：顯示最多 3 位小數，然後加上千分位符號
            formatted = f"{value:,.3f}".rstrip("0").rstrip(".")
            return formatted
        else:
            # 小於 1：找第一個非零後的兩位小數（最多 10 位精度）
            str_value = f"{value:.10f}"
            decimal_part = str_value.split('.')[1]
            non_zero_index = next((i for i, digit in enumerate(decimal_part) if digit != '0'), len(decimal_part))
            end_index = non_zero_index + 3  # 非零數字 + 後兩位小數
            formatted_decimal = decimal_part[:end_index].rstrip("0").rstrip(".")
            return f"0.{formatted_decimal}"
    except (ValueError, TypeError):
        return str(value)


def crypto_list(request):
    query = request.GET.get('query', '') 
    sort_by = request.GET.get('sort_by')  # 排序欄位
    sort_order = request.GET.get('sort_order')  # 排序狀態（"asc", "desc", "default"）

    if query:
        all_prices = BitcoinPrice.objects.filter(coin__coinname__icontains=query)
    else:
        all_prices = BitcoinPrice.objects.all()

    # 根據排序狀態進行排序
    if sort_by and sort_order == 'asc':
        all_prices = all_prices.order_by(sort_by)  # A-Z 排序
    elif sort_by and sort_order == 'desc':
        all_prices = all_prices.order_by(F(sort_by).desc())  # Z-A 排序
    else:
        # 預設根據 market_cap 由大到小排序
        all_prices = all_prices.order_by('-market_cap')

    paginator = Paginator(all_prices, 40)  # 每頁顯示10條數據
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 格式化價格數據
    for price in page_obj.object_list:
        price.usd_display = format_crypto_price(price.usd)
        price.twd_display = format_crypto_price(price.twd)
        price.jpy_display = format_crypto_price(price.jpy)
        price.eur_display = format_crypto_price(price.eur)
        price.volume_24h_display = format_crypto_price(price.volume_24h)
        price.market_cap_display = format_crypto_price(price.market_cap)

    if request.user.is_authenticated:
        user_profile = request.user.profile
        favorite_coin_ids = list(user_profile.favorite_coin.values_list('id', flat=True))
    else:
        favorite_coin_ids = []

    return render(request, 'crypto_list.html', {
        'page_obj': page_obj,
        'sort_by': sort_by,
        'sort_order': sort_order,
        'favorite_coin_ids': favorite_coin_ids,
    })

def crypto_prices_ajax(request):
    query = request.GET.get('query', '') 
    sort_by = request.GET.get('sort_by')  
    sort_order = request.GET.get('sort_order')

    if query:
        prices = BitcoinPrice.objects.filter(coin__coinname__icontains=query)
    else:
        prices = BitcoinPrice.objects.all()

    if sort_by and sort_order == 'asc':
        prices = prices.order_by(sort_by)
    elif sort_by and sort_order == 'desc':
        prices = prices.order_by(F(sort_by).desc())
    else:
        prices = prices.order_by('-market_cap')

    # 只取前40筆，避免一次回傳太多資料
    prices = prices.all()

    # 準備回傳的資料格式
    data = []
    for price in prices:
        data.append({
            'id': price.id,
            'coin_name': price.coin.coinname,
            'usd': format_crypto_price(price.usd),
            'twd': format_crypto_price(price.twd),
            'jpy': format_crypto_price(price.jpy),
            'eur': format_crypto_price(price.eur),
            'volume_24h': format_crypto_price(price.volume_24h),
            'market_cap': format_crypto_price(price.market_cap),
        })

    return JsonResponse({'prices': data,'sort_by': sort_by,'sort_order': sort_order,})

from django.shortcuts import render, redirect
from .forms import UserProfileForm
from django.contrib.auth.decorators import login_required

@login_required
def upload_profile_image(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            # 取得上傳的圖片
            image = request.FILES.get('profile_image')

            # 如果有圖片上傳，進行處理
            if image:
                # 使用 Pillow 處理圖片
                img = Image.open(image)

                # 將圖片轉換為 RGB 格式，並保存為 JPG
                img = img.convert('RGB')

                # 設定最大寬度與高度（可根據需要調整）
                max_width = 500
                max_height = 500
                img.thumbnail((max_width, max_height))

                # 保存為 JPG 格式
                image_io = BytesIO()
                img.save(image_io, format='JPEG')
                image_io.seek(0)

                # 將處理過的圖片轉為 Django 可以儲存的 ContentFile
                image_name = f"{image.name.split('.')[0]}.jpg"  # 保留原檔名，但轉為 .jpg
                user_profile_image = ContentFile(image_io.read(), name=image_name)

                # 更新用戶檔案中的圖片
                request.user.profile.profile_image.save(image_name, user_profile_image)

            # 提交表單後，跳轉到主頁
            return redirect('user_profile')  # 或者你可以跳轉到其他頁面
    else:
        form = UserProfileForm(instance=request.user.profile)

    return render(request, 'user_profile.html', {'form': form})

@login_required
def add_to_favorites(request, pk):
    user_profile = request.user.profile
    try:
        crypto = Coin.objects.get(id=pk)
        user_profile.favorite_coin.add(crypto)
        user_profile.save()
        return JsonResponse({'status': 'success', 'action': 'add'})
    except Coin.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Coin not found'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
def remove_from_favorites(request, pk):
    user_profile = request.user.profile
    coin = get_object_or_404(Coin, id=pk)

    # 移除最愛
    user_profile.favorite_coin.remove(coin)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})

    return redirect('favorite_coins')  # 如果不是 AJAX 請求，重定向回我的最愛頁面

@login_required
def favorite_coins(request):
    user_profile = request.user.profile
    favorite_cryptos = user_profile.favorite_coin.all()  # 獲取用戶的最愛幣
    return render(request, 'favorite_coins.html', {'favorite_cryptos': favorite_cryptos})

#忘記密碼
# from django.contrib.auth import views as auth_views
# from django.urls import reverse_lazy
# from django.contrib.auth import get_user_model

# class CustomPasswordResetView(auth_views.PasswordResetView):
#     template_name = 'password_reset_form.html'  # 忘記密碼表單
#     email_template_name = 'password_reset_email.html'  # 發送郵件的模板
#     success_url = reverse_lazy('password_reset_done')  # 成功後跳轉到 `password_reset_done`

# class CustomPasswordResetDoneView(auth_views.PasswordResetDoneView):
#     template_name = 'password_reset_done.html'  # 提示郵件已發送的頁面

# class CustomPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
#     template_name = 'password_reset_confirm.html'  # 用戶輸入新密碼的頁面
#     success_url = reverse_lazy('password_reset_complete')  # 成功設置新密碼後跳轉的頁面

# class CustomPasswordResetCompleteView(auth_views.PasswordResetCompleteView):
#     template_name = 'password_reset_complete.html'  # 密碼重設完成後的頁面

#重設密碼
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from django.shortcuts import render, redirect
from django.contrib import messages 

@login_required
def update_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('password')
        confirm_password = request.POST.get('password_confirm')

        user = request.user

        if not check_password(current_password, user.password):
            messages.error(request, '目前密碼不正確。', extra_tags='password')
            return redirect('user_profile')

        if new_password != confirm_password:
            messages.error(request, '新密碼與確認密碼不一致。', extra_tags='password')
            return redirect('user_profile')

        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)

        messages.success(request, '密碼已成功修改。', extra_tags='password')
        return redirect('user_profile')

    return render(request, 'user_profile.html')

@login_required
def update_firstname(request):
    if request.method == 'POST':
        new_firstname = request.POST.get('firstname')

        user = request.user

        if not new_firstname.strip():
            messages.error(request, '名稱不可為空。', extra_tags='firstname')
            return redirect('user_profile')  # 替換為你的對應路由名稱

        user.first_name = new_firstname
        user.save()

        messages.success(request, '名稱已成功修改。', extra_tags='firstname')
        return redirect('user_profile')  # 替換為你的對應路由名稱

    # GET 請求時返回對應的頁面
    return render(request, 'user_profile.html')



# 新聞推送
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import UserNotificationPreference


@login_required
def update_notification_preferences(request):
    # 設置更新通知的邏輯
    if request.method == 'POST':
        news_notifications = request.POST.get('news_notifications') == 'on'
        email_notifications = request.POST.get('email_notifications') == 'on'
        site_notifications = request.POST.get('site_notifications') == 'on'

        preference, created = UserNotificationPreference.objects.get_or_create(user=request.user)
        preference.news_notifications = news_notifications
        preference.email_notifications = email_notifications
        preference.site_notifications = site_notifications
        preference.save()

        messages.success(request, '通知設定已更新！')
        return redirect('user_profile')  # 更新後返回用戶設定頁面

    return redirect('user_profile')  # 如果不是 POST 請求，則重定向回首頁或其他頁面


from django.template.loader import render_to_string
from django.http import HttpResponse
from django.core.mail import send_mail

def send_email_news(request):
    # 获取所有用户
    users = User.objects.all()
    users = User.objects.filter(notification_preference__email_notifications=True)    
    if not users.exists():
    # 查詢結果不為空，執行某些操作
        return HttpResponse("Hello, world!")
    
    latest_articles = NewsArticle.objects.all().order_by('-time')[:1000]


    # 遍历所有用户并发送邮件
    for user in users:
        subject = '新聞通知'
        

        # 使用模板渲染 HTML 邮件内容
        html_content = render_to_string('email_template.html', {
            'subject': subject,
            'name': user.username,  # 假设你希望使用用户名来定制邮件内容
            'latest_articles':latest_articles,
        })

        # 使用 send_mail 发送邮件
        send_mail(
            subject,              # 邮件主题
            "",              # 邮件文本内容
            None, # 发件人邮箱，或者可以从 settings.py 获取
            [user.email],         # 收件人邮箱（每个用户的邮箱）
            html_message=html_content,  # 设置 HTML 内容
        )

    return render(request, 'email_template.html', {'subject':subject,'latest_articles': latest_articles,'name': user.username})

'''
import numpy as np
import pandas as pd
from data_analysis.prediction.btc import predict_crypto_price
import json
def crypto_price_chart(request):
    coin = Coin.objects.get(coinname="Bitcoin")
    recent_data = (
        CoinHistory.objects.filter(coin=coin)
        .order_by("-date")[:24]  # 取最近 24 小時
        .values("date", "close_price", "high_price", "low_price", "open_price", "volume")
    )

    # 轉換為 DataFrame
    df = pd.DataFrame(list(recent_data))
    df = df.sort_values("date")  # 依時間排序

    # 確保 date 欄位是 datetime 類型
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")  # 依時間排序
    # 預測價格
    predicted_price = predict_crypto_price(df[["close_price", "high_price", "low_price", "open_price", "volume"]])
    print(df["date"].iloc[-1] + pd.Timedelta(hours=1))
    # 構造 JSON 返回給前端
    data = {
        "labels": df["date"].dt.strftime("%Y-%m-%d %H:%M:%S").tolist() + [(df["date"].iloc[-1] + pd.Timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")],  # 加入預測時間
        "prices": df["close_price"].tolist(),  # 歷史價格
        "predicted_price": {"date": df["date"].iloc[-1] + pd.Timedelta(hours=1), "price": predicted_price},
    }


    return render(request, "chart.html", {"chart_data": json.dumps(data , default=str)})
'''
def crypto_price_chart(request):
    return HttpResponse("hello")


def crypto_detail(request, coin_id):
    coin = get_object_or_404(Coin, id=coin_id)

    # 最新價格資料
    latest_price = BitcoinPrice.objects.filter(coin=coin).order_by('-timestamp').first()

    # 最新歷史資料（K 線）
    latest_history = CoinHistory.objects.filter(coin=coin).order_by('-date').first()

    return render(request, 'crypto_detail.html', {
        'coin_id': coin_id,
        'data': coin,  # 原本叫 data 的其實是 coin
        'coin': coin,  # 提供給 include 用
        'latest_price': latest_price,
        'latest_history': latest_history
    })

from django.db.models import Min, Max, Sum, Subquery, OuterRef,Avg
from django.db.models.functions import TruncMinute, TruncHour, TruncDay, TruncWeek, TruncMonth
from django.http import JsonResponse
from .models import CoinHistory
from django.db.models import F, ExpressionWrapper, DateTimeField, Func, IntegerField
import time
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware
import pytz


def coin_history(request, coin_id):
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')
    limit = 1500  # 新增 limit 參數，預設取 500 筆

    if not start_str or not end_str:
        return JsonResponse({'error': '缺少 start 或 end 參數'}, status=400)

    start = parse_datetime(start_str)
    end = parse_datetime(end_str)

    if not start or not end:
        return JsonResponse({'error': 'start 或 end 參數格式錯誤'}, status=400)

    if start >= end:
        return JsonResponse({'error': 'start 需早於 end'}, status=400)

    # 查詢資料並限制筆數
    qs = (
        CoinHistory.objects.filter(
            coin_id=coin_id,
            date__gte=start,
            date__lte=end
        )
        .order_by('date')[:limit]  # 取最新 N 筆
    )
    records = list(qs)
    data = [
        {
            "date": int(item.date.timestamp() * 1000),  # amCharts 需要毫秒時間戳
            "open": float(item.open_price),
            "high": float(item.high_price),
            "low": float(item.low_price),
            "close": float(item.close_price),
            "volume": float(item.volume),
        }
        for item in records
    ]


    if 1 <= coin_id <= 10:
        interval = "minute"
    else:
        interval = "day"
    
    return JsonResponse({"data": data, "interval": interval})

@login_required
def delete_account(request):
    if request.method == "POST":
        password = request.POST.get("password_confirm")
        user = request.user

        if not user.check_password(password):  # 驗證密碼是否正確
            messages.error(request, "密碼錯誤，請重新輸入！")
            return redirect("user_profile")

        messages.success(request, "您的帳號已成功刪除！")
        logout(request)
        user.delete()
        return redirect("home")

    return redirect("user_profile")
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
from .models import UserProfile

@login_required
def membership_plans(request):
    return render(request, 'membership_plans.html')

@login_required
@csrf_exempt
def process_payment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            plan = data.get('plan')
            card_number = data.get('cardNumber')
            expiration_date = data.get('expirationDate')
            cvv = data.get('cvv')

            if not card_number or not expiration_date or not cvv:
                return JsonResponse({'success': False, 'message': '支付資訊不完整'})

            if plan not in ['monthly', 'yearly']:
                return JsonResponse({'success': False, 'message': '無效的方案'})

            # 假設支付成功（這裡應該整合 Stripe/PayPal 等）
            if card_number.startswith("4242"):  
                user_profile = request.user.profile
                user_profile.membership = 'premium'
                user_profile.save()
                return JsonResponse({'success': True, 'message': '支付成功，已升級為 Premium 會員！'})
            else:
                return JsonResponse({'success': False, 'message': '支付失敗，請檢查信用卡資訊'})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': '請求格式錯誤'})

    return JsonResponse({'success': False, 'message': '無效的請求方式'})


@login_required
def upgrade_to_premium(request):
    if request.method == 'POST':
        user = request.user.profile
        print(user)
        user.membership = 'premium'
        user.save()

        return JsonResponse({'success': True})
    return JsonResponse({'success': False})




from django.utils import timezone
from .models import SignIn
@login_required
def sign_in(request):
    user = request.user
    today = timezone.now().date()

    # 确保每个用户在数据库中都有一条签到记录，如果没有则自动创建
    sign_in_record, created = SignIn.objects.get_or_create(user=user)

    # 如果今天已经签到过了
    if sign_in_record.last_sign_in_date == today:
        messages.info(request, "今天已簽到過，請明天再來！")
        return redirect('user_profile')

    # 否则，进行签到
    sign_in_record.update_consecutive_sign_in()  # 更新连续签到次数
    sign_in_record.last_sign_in_date = today
    sign_in_record.sign_in_count += 1
    sign_in_record.save()

    messages.success(request, "簽到成功！")
    referer = request.META.get('HTTP_REFERER', '/')
    return redirect(referer)

@login_required
def user_profile(request):
    today = timezone.now().date()
    return render(request, 'myapp/user_profile.html', {'today': today})

#使用者條款
from django.shortcuts import render

def user_terms(request):
    return render(request, 'user_terms.html')




from django.shortcuts import render

def guanggao_shenfen_queren(request):
    # 預設顯示廣告
    ad_show = True

    # 檢查用戶是否已登入並且是 premium 用戶
    if request.user.is_authenticated:
        # 確保用戶有 Profile
        try:
            user_profile = request.user.profile
            if user_profile.membership == 'premium':
                ad_show = True  # premium 用戶不顯示廣告
        except user_profile.DoesNotExist:
            ad_show = True  # 如果沒有 profile，預設為 free 用戶，顯示廣告
    else:
        ad_show = True  # 未登入用戶視為 free，用戶，顯示廣告

    # 返回渲染頁面並傳遞 ad_show 變數
    return render(request, 'home.html', {'ad_show': ad_show})

from django.shortcuts import render
from django.db.models import OuterRef, Subquery
from .models import Coin, BitcoinPrice

def favorite_coins(request):
    if not request.user.is_authenticated:
        return render(request, 'favorites.html', {'favorite_cryptos': []})

    # 取最新價格資料
    latest_price = BitcoinPrice.objects.filter(
        coin=OuterRef('pk')
    ).order_by('-timestamp')

    # 注入最新價格欄位
    favorite_cryptos = request.user.profile.favorite_coin.annotate(
        usd_display=Subquery(latest_price.values('usd')[:1]),
        market_cap_display=Subquery(latest_price.values('market_cap')[:1]),
        volume_24h_display=Subquery(latest_price.values('volume_24h')[:1]),
        change_24h=Subquery(latest_price.values('change_24h')[:1])
    )

    return render(request, 'favorite_coins.html', {
        'favorite_cryptos': favorite_cryptos
    })

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from main.models import UserProfile, BitcoinPrice, Coin

@login_required
def favorite_coins(request):
    # 取得使用者收藏的幣種
    profile = request.user.profile
    favorite_coins = profile.favorite_coin.all()

    favorite_cryptos = []
    for coin in favorite_coins:
        # 取得最新價格資料
        latest_price = BitcoinPrice.objects.filter(coin=coin).order_by('-timestamp').first()
        if latest_price:
            favorite_cryptos.append({
                'id': coin.id,
                'coinname': coin.coinname,
                'logo_url': coin.logo_url,
                'usd_display': "{:,.2f}".format(latest_price.usd),
                'market_cap_display': "{:,.2f}".format(latest_price.market_cap or 0),
                'volume_24h_display': "{:,.2f}".format(latest_price.volume_24h or 0),
                'change_24h': latest_price.change_24h or 0,
            })
        else:
            # 沒有價格資料時填 0
            favorite_cryptos.append({
                'id': coin.id,
                'coinname': coin.coinname,
                'logo_url': coin.logo_url,
                'usd_display': "0.00",
                'market_cap_display': "0.00",
                'volume_24h_display': "0.00",
                'change_24h': 0,
            })

    context = {
        'favorite_cryptos': favorite_cryptos,
    }
    return render(request, 'favorite_coins.html', context)



@login_required
def submit_questionnaire(request):
    print("收到 POST：", request.POST)
    if request.method == "POST":
        user = request.user

        for key in request.POST:
            if key.startswith("question_"):
                question_id = key.split("_")[1]
                try:
                    question = FeedbackQuestion.objects.get(pk=question_id)
                except FeedbackQuestion.DoesNotExist:
                    continue

                if question.question_type == "checkbox":
                    # 多選題：取得所有選項值
                    answers = request.POST.getlist(key)
                    for ans in answers:
                        FeedbackAnswer.objects.create(
                            user=user,
                            question=question,
                            answer_text=ans,
                            submitted_at=now()
                        )
                else:
                    # 單選 / 滿意度 / 下拉選單 / 開放填答
                    answer = request.POST.get(key)
                    print(f"儲存：user={user}, question={question.id}, answer={answer}")
                    if answer:
                        FeedbackAnswer.objects.create(
                            user=user,
                            question=question,
                            answer_text=answer,
                            submitted_at=now()
                        )

        return redirect('/')

@csrf_exempt
def track_impression(request):
    data = json.loads(request.body)
    page = data.get("page", "/")
    tracker, _ = PageTracker.objects.get_or_create(page_name=page)
    tracker.impressions += 1
    tracker.save()
    return JsonResponse({'status': 'ok'})

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

def coin_history_api(request):
    coin_id = request.GET.get('coin_id')
    if not coin_id:
        return JsonResponse({'error': '缺少 coin_id 參數'}, status=400)

    try:
        selected_coin = Coin.objects.get(id=coin_id)
    except Coin.DoesNotExist:
        return JsonResponse({'error': '查無此幣種'}, status=404)

    thirty_days_ago = timezone.now().date() - timedelta(days=5)

    queryset = (
        CoinHistory.objects
        .filter(coin_id=coin_id, date__gte=thirty_days_ago)
        .select_related('coin')
        .order_by('date')
    )

    fields = ['date', 'close_price', 'high_price', 'low_price', 'volume']
    print(fields)  # 確認沒有空字串

    # 1️⃣ 先把 queryset 讀成 DataFrame
    df = pd.DataFrame.from_records(queryset.values(*fields))

    # 2️⃣ 再把數值欄位轉成 float，避免 Decimal 與 float 運算錯誤
    for col in ['close_price', 'high_price', 'low_price', 'volume']:
        if col in df.columns:
            df[col] = df[col].astype(float)

    

    if df.empty:
        return JsonResponse({'error': '此時間區間無資料'}, status=204)

    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')

    df['ema20'] = ta.trend.EMAIndicator(close=df['close_price'], window=20).ema_indicator()
    df['rsi'] = ta.momentum.RSIIndicator(close=df['close_price'], window=14).rsi()
    df = df.dropna(subset=['ema20', 'rsi'])

    bb = ta.volatility.BollingerBands(close=df['close_price'], window=20, window_dev=2)
    df['bb_high'] = bb.bollinger_hband()
    df['bb_low'] = bb.bollinger_lband()

    stoch = ta.momentum.StochasticOscillator(
        high=df['high_price'], low=df['low_price'], close=df['close_price'], window=14
    )
    df['stoch'] = stoch.stoch()

    df['cci'] = ta.trend.CCIIndicator(
        high=df['high_price'], low=df['low_price'], close=df['close_price'], window=20
    ).cci()

    df['williams_r'] = ta.momentum.WilliamsRIndicator(
        high=df['high_price'], low=df['low_price'], close=df['close_price'], lbp=14
    ).williams_r()

    df['obv'] = ta.volume.OnBalanceVolumeIndicator(close=df['close_price'], volume=df['volume']).on_balance_volume()
    df['mfi'] = ta.volume.MFIIndicator(
        high=df['high_price'], low=df['low_price'], close=df['close_price'], volume=df['volume'], window=14
    ).money_flow_index()

    df['atr'] = ta.volatility.AverageTrueRange(
        high=df['high_price'], low=df['low_price'], close=df['close_price'], window=14
    ).average_true_range()

    interval = int(request.GET.get('interval', 60))  # 預設 60
    if interval > 1:
        df = df.iloc[::interval, :].reset_index(drop=True)

    import math

    def safe_list(values):
        """把 NaN 或 None 轉成 None，方便 JSON 回傳"""
        return [v if v is not None and not (isinstance(v, float) and math.isnan(v)) else None for v in values]


    chart_data = {
        'coin_id': int(coin_id),
        'selected_coin_name': selected_coin.coinname,
        'dates': df['date'].dt.strftime('%Y-%m-%d').tolist(),

        # 價格相關
        'close': safe_list(df['close_price'].tolist()),
        'ema20': safe_list(df['ema20'].round(2).tolist()),
        'bb_high': safe_list(df['bb_high'].round(2).tolist()),
        'bb_low': safe_list(df['bb_low'].round(2).tolist()),

        # 動能指標
        'rsi': safe_list(df['rsi'].round(2).tolist()),
        'stoch': safe_list(df['stoch'].round(2).tolist()),
        'cci': safe_list(df['cci'].round(2).tolist()),
        'williams_r': safe_list(df['williams_r'].round(2).tolist()),

        # 成交量
        'obv': safe_list(df['obv'].round(2).tolist()),
        'mfi': safe_list(df['mfi'].round(2).tolist()),

        # 波動率
        'atr': safe_list(df['atr'].round(2).tolist())
    }

    return JsonResponse(chart_data, encoder=DecimalEncoder, safe=False)


import os
import pandas as pd
import numpy as np
import traceback
import joblib
from django.http import JsonResponse
from sklearn.ensemble import RandomForestClassifier

def strategy_ema_cross(df: pd.DataFrame) -> pd.DataFrame:
    """短期 EMA10 追蹤中期 EMA20 的趨勢追蹤策略。"""
    
    # 買入/做多訊號 (1): EMA10 上穿 EMA20 (趨勢轉強)
    condition_buy = (df['ema10'].shift(1) < df['ema20'].shift(1)) & \
                    (df['ema10'] > df['ema20'])

    # 賣出/平倉訊號 (-1): EMA10 跌破 EMA20 (趨勢轉弱)
    condition_sell = (df['ema10'].shift(1) > df['ema20'].shift(1)) & \
                     (df['ema10'] < df['ema20'])
    
    df.loc[condition_buy, 'pred'] = 1
    df.loc[condition_sell, 'pred'] = -1 
    
    return df

def strategy_rsi_reversion(df: pd.DataFrame) -> pd.DataFrame:
    """RSI 超買超賣反轉策略 (適用於盤整/震盪市場)。"""
    
    # 買入/做多訊號 (1): RSI < 30 (超賣區)
    condition_buy = (df['rsi'] < 30)

    # 賣出/平倉訊號 (-1): RSI > 70 (超買區)
    condition_sell = (df['rsi'] > 70)
    
    df.loc[condition_buy, 'pred'] = 1
    df.loc[condition_sell, 'pred'] = -1 
    
    return df

def strategy_macd_cross(df: pd.DataFrame) -> pd.DataFrame:
    """MACD 趨勢策略：DIF 上穿 DEA → 做多；下穿 → 平倉。"""
    # MACD 計算
    ema12 = df['close_price'].ewm(span=12, adjust=False).mean()
    ema26 = df['close_price'].ewm(span=26, adjust=False).mean()
    df['macd_dif'] = ema12 - ema26
    df['macd_dea'] = df['macd_dif'].ewm(span=9, adjust=False).mean()
    
    # 上穿做多、下穿平倉
    condition_buy = (df['macd_dif'].shift(1) < df['macd_dea'].shift(1)) & (df['macd_dif'] > df['macd_dea'])
    condition_sell = (df['macd_dif'].shift(1) > df['macd_dea'].shift(1)) & (df['macd_dif'] < df['macd_dea'])
    
    df.loc[condition_buy, 'pred'] = 1
    df.loc[condition_sell, 'pred'] = -1
    return df

def strategy_donchian_breakout(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    """Donchian Channel 突破策略：突破過去 N 日高點買進，跌破低點賣出。"""
    df['donchian_high'] = df['high_price'].rolling(n).max()
    df['donchian_low'] = df['low_price'].rolling(n).min()

    condition_buy = df['close_price'] > df['donchian_high'].shift(1)
    condition_sell = df['close_price'] < df['donchian_low'].shift(1)

    df.loc[condition_buy, 'pred'] = 1
    df.loc[condition_sell, 'pred'] = -1
    return df

def strategy_roc_momentum(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """ROC/Momentum 動能策略：動能轉強時做多。"""
    df['roc'] = df['close_price'].pct_change(n)
    condition_buy = df['roc'] > 0
    condition_sell = df['roc'] < 0
    df.loc[condition_buy, 'pred'] = 1
    df.loc[condition_sell, 'pred'] = -1
    return df

def strategy_obv_trend(df: pd.DataFrame) -> pd.DataFrame:
    """OBV 趨勢策略：OBV 上升 → 多方強勢。"""
    df['obv'] = np.where(df['close_price'] > df['close_price'].shift(1),
                         df['volume'], 
                         np.where(df['close_price'] < df['close_price'].shift(1), -df['volume'], 0))
    df['obv'] = df['obv'].cumsum()

    condition_buy = df['obv'] > df['obv'].shift(1)
    condition_sell = df['obv'] < df['obv'].shift(1)

    df.loc[condition_buy, 'pred'] = 1
    df.loc[condition_sell, 'pred'] = -1
    return df


# ====================================================================
# 策略核心計算邏輯 (Strategy Dispatcher & Reward Calculation)
# ====================================================================

def calculate_strategy_performance(df: pd.DataFrame, strategy_name: str) -> pd.DataFrame:
    """
    安全版回測函數：
    - 使用前一日訊號延續持倉
    - 處理 NaN，不用 0 填充
    - 計算累積報酬 cum_strategy / cum_buy_hold
    """
    # 初始化 pred 欄位
    df['pred'] = 0

    # 選擇策略
    if strategy_name == 'EMA_CROSS':
        df = strategy_ema_cross(df)
    elif strategy_name == 'RSI_REVERSION':
        df = strategy_rsi_reversion(df)
    elif strategy_name == 'MACD_CROSS':
        df = strategy_macd_cross(df)
    elif strategy_name == 'DONCHIAN_BREAKOUT':
        df = strategy_donchian_breakout(df)
    elif strategy_name == 'ROC_MOMENTUM':
        df = strategy_roc_momentum(df)
    elif strategy_name == 'OBV_TREND':
        df = strategy_obv_trend(df)
    else:
        raise ValueError(f"Strategy {strategy_name} not found.")

    # -----------------------------
    # 計算報酬
    # -----------------------------
    df['return'] = df['close_price'].pct_change().fillna(0)

    # -----------------------------
    # 持倉管理 (前一日訊號延續)
    # -----------------------------
    df['position'] = 0
    for i in range(1, len(df)):
        if df['pred'].iloc[i] == 1:       # 開多
            df['position'].iloc[i] = 1
        elif df['pred'].iloc[i] == -1:    # 平倉
            df['position'].iloc[i] = 0
        else:                             # 延續前一日持倉
            df['position'].iloc[i] = df['position'].iloc[i-1]

    # 隔日生效
    df['position'] = df['position'].shift(1).fillna(0)

    # 策略報酬
    df['strategy_return'] = df['position'] * df['return']

    # 累積報酬
    df['cum_strategy'] = (1 + df['strategy_return']).cumprod()
    df['cum_buy_hold'] = (1 + df['return']).cumprod()

    # 初始化第一個有效值為 1
    first_valid_index = df['cum_strategy'].first_valid_index()
    if first_valid_index is not None:
        df.loc[first_valid_index, 'cum_strategy'] = 1.0
        df.loc[first_valid_index, 'cum_buy_hold'] = 1.0

    return df


def backtest_view(request):
    try:
        # ... (省略 coin_id 獲取和錯誤檢查部分)
        coin_param = request.GET.get('coin_id')
        if not coin_param:
            return JsonResponse({'error': '缺少 coin_id 參數'}, status=400)
        try:
            coin_list = [int(c.strip()) for c in coin_param.split(',')]
        except ValueError:
            return JsonResponse({'error': 'coin_id 格式錯誤，請傳入數字列表'}, status=400)
        
        print("💡 模型部分已移除，將使用自定義 RSI/EMA/BBANDS 策略替代。")

        interval = int(request.GET.get('interval', 60))
        # 獲取要回測的策略名稱，預設為 EMA_CROSS
        strategy_to_test = request.GET.get('strategy', 'EMA_CROSS')

        strategies = [
            'EMA_CROSS', 'RSI_REVERSION','MACD_CROSS', 
            'DONCHIAN_BREAKOUT', 'ROC_MOMENTUM', 'OBV_TREND'
        ]

        result_data = {}
        # 數據長度設定：回測過去 7 天的數據
        thirty_days_ago = timezone.now().date() - timedelta(days=7) 

        for coin_id in coin_list:
            try:
                selected_coin = Coin.objects.get(id=coin_id)
            except Coin.DoesNotExist:
                continue

            # 查詢 CoinHistory 數據 (省略查詢細節)
            queryset = (
                CoinHistory.objects
                .filter(coin_id=coin_id, date__gte=thirty_days_ago)
                .select_related('coin')
                .order_by('date')
            )
            fields = ['date', 'close_price', 'high_price', 'low_price', 'volume']
            df = pd.DataFrame.from_records(queryset.values(*fields))

            if df.empty or len(df) < 30:
                print(f"Coin {coin_id}: 數據不足，跳過。")
                continue

            # 將 Decimal 欄位轉 float (省略細節)
            for col in ['close_price', 'high_price', 'low_price', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce').astype(float) 

            # ========================================================
            # ✅ 擴充技術指標計算，支援所有已定義的策略
            # ========================================================
            # EMA (用於 EMA_CROSS)
            df["ema20"] = df["close_price"].ewm(span=20, adjust=False).mean()
            df["ema10"] = df["close_price"].ewm(span=10, adjust=False).mean()

            # RSI (用於 RSI_REVERSION)
            delta = df["close_price"].diff()
            gain = np.where(delta > 0, delta, 0)
            loss = np.where(delta < 0, -delta, 0)
            avg_gain = pd.Series(gain).rolling(window=14).mean()
            avg_loss = pd.Series(loss).rolling(window=14).mean()
            with np.errstate(divide='ignore', invalid='ignore'):
                 rs = avg_gain / (avg_loss + 1e-10) 
            df["rsi"] = 100 - (100 / (1 + rs))
            df['rsi'] = df['rsi'].fillna(0)
            
            # 🆕 Bollinger Bands (用於 BBANDS_REVERSION)
            df["ma20"] = df["close_price"].rolling(20).mean()
            df["std20"] = df["close_price"].rolling(20).std()
            df["bb_upper"] = df["ma20"] + 2 * df["std20"]
            df["bb_lower"] = df["ma20"] - 2 * df["std20"]

            # ========================================================

            if interval > 1:
                df = df.iloc[::interval, :].reset_index(drop=True)

            coin_result = {}

            # ✅ 傳入選定的策略名稱
            for strat in strategies:
                g = calculate_strategy_performance(df.copy(), strat)  # ⚡ 注意要 copy 避免 df 被改
                coin_result[strat] = {
                    "dates": g["date"].dt.strftime("%Y-%m-%d").tolist(),
                    "strategy": g["cum_strategy"].astype(float).tolist(),
                    "buy_hold": g["cum_buy_hold"].astype(float).tolist(),

                    # 新增分析指標👇
                    "final_strategy_return": float(g["cum_strategy"].iloc[-1]),   # 策略最終報酬率 (%)
                    "final_buy_hold_return": float(g["cum_buy_hold"].iloc[-1]),   # Buy & Hold 報酬率 (%)
                    "max_drawdown": float(((g["cum_strategy"] / g["cum_strategy"].cummax()) - 1).min() * 100),  # 最大回撤 (%)
                    "win_rate": float((g["pred"] == 1).sum() / len(g["pred"]) * 100),  # 做多次數比例 (%)
                    "trade_count": int(((g['pred'] != 0) & (g['pred'] != g['pred'].shift(1))).sum()),  # 交易次數
                    "avg_gain_per_trade": float(g.loc[g['pred'] == 1, 'close_price'].pct_change().mean() * 100),  # 平均獲利 (%)
                    "volatility": float(g['close_price'].pct_change().std() * np.sqrt(252) * 100),  # 年化波動率 (%)
                    "sharpe_ratio": float((g['close_price'].pct_change().mean() / g['close_price'].pct_change().std()) * np.sqrt(252)),  # 夏普比率
                }
            
            # ... (省略結果處理和 GPT 分析部分，保持原有邏輯)
            if g['cum_strategy'].empty:
                print(f"Coin {coin_id}: 策略回測失敗。")
                continue

            # g_final = coin_result[strategy_to_test]
            # strategy_pct = (g_final["strategy"][-1] - 1) * 100
            # buy_hold_pct = (g_final["buy_hold"][-1] - 1) * 100

            strategy_results = {}
            for strat_name, strat_data in coin_result.items():
                strategy_results[strat_name] = {
                    "strategy_pct": (strat_data["strategy"][-1] - 1) * 100,
                    "buy_hold_pct": (strat_data["buy_hold"][-1] - 1) * 100,
                    "max_drawdown": strat_data["max_drawdown"],
                    "sharpe_ratio": strat_data["sharpe_ratio"],
                    "volatility": strat_data["volatility"],
                    "win_rate": strat_data["win_rate"],
                    "trade_count": strat_data["trade_count"],
                    "avg_gain_per_trade": strat_data["avg_gain_per_trade"],
                }

            df_plot = df.dropna(subset=["bb_upper", "bb_lower"]).reset_index(drop=True)

            result_data[coin_id] = {
                "coin_name": selected_coin.coinname,
                "dates": g["date"].dt.strftime("%Y-%m-%d").tolist(),
                "strategy": coin_result, 
                "buy_hold": g["cum_buy_hold"].astype(float).tolist(),
                "close": g["close_price"].astype(float).tolist(),
                "ema20": g["ema20"].astype(float).fillna(0).tolist(),
                "ema10": g["ema10"].astype(float).fillna(0).tolist(),
                "rsi": g["rsi"].astype(float).fillna(0).tolist(),
                # 新增 BBands 輸出以便除錯
                "bb_upper": df_plot["bb_upper"].tolist(),
                "bb_lower": df_plot["bb_lower"].tolist(),
                "strategies": strategy_results
            }

        # ... (省略 GPT 分析部分)
        if not result_data:
            return JsonResponse({'error': '無有效數據進行回測和分析'}, status=404)
        
        summary_data = {
            coin_id: {
                "coin_name": v["coin_name"],
                "strategies": {
                    strat_name: {
                        "strategy_pct": round(s.get("strategy_pct", 0), 2),
                        "buy_hold_pct": round(s.get("buy_hold_pct", 0), 2),
                        "max_drawdown": round(s.get("max_drawdown", 0), 2),
                        "sharpe_ratio": round(s.get("sharpe_ratio", 0), 2),
                        "volatility": round(s.get("volatility", 0), 2),
                        "win_rate": round(s.get("win_rate", 0), 2),
                        "trade_count": int(s.get("trade_count", 0)),
                        "avg_gain_per_trade": round(s.get("avg_gain_per_trade", 0), 2)
                    }
                    for strat_name, s in v["strategies"].items()
                }
            }
            for coin_id, v in result_data.items()
        }

        print(summary_data)

        analysis_prompt = f"""
            以下是加密貨幣在過去 7 天回測的摘要數據（單位：%）：
            {json.dumps(summary_data, ensure_ascii=False, indent=2)}

            本次使用的策略包括：
            {', '.join(strategies)}

            請你根據以上資料，進行以下分析（請用中文、條列重點）：

            各幣種「策略績效」與「Buy & Hold」的最終報酬率比較。  
            評估每個幣種的策略表現是否優於 Buy & Hold（請指出差距百分比）。  
            分析各策略在整體上的表現特徵（例如：哪種策略適合震盪盤、哪種在趨勢盤效果好）。  
            指出「整體表現最佳」與「表現最差」的幣種與策略。  
            提供投資建議，包括：  
            - 是否建議持續使用該策略  
            - 是否適合長期持有  
            - 潛在風險或改進建議  

            請用清晰、條列式方式回答，若有數據差異，請明確指出（例如：策略報酬率比 Buy & Hold 高 3.2%）。
            """

        url = "https://free.v36.cm/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api}",
            "Content-Type": "application/json",
        }
        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "你是一位專業的加密貨幣投資顧問。"},
                {"role": "user", "content": analysis_prompt}
            ]
        }
        
        gpt_response = requests.post(url, headers=headers, json=data)
        gpt_response.raise_for_status()

        gpt_result = gpt_response.json()
        gpt_reply = gpt_result.get("choices", [{}])[0].get("message", {}).get("content", "GPT 分析失敗或內容為空。")

        return JsonResponse({
            "result_data": result_data,
            "gpt_analysis": gpt_reply
        })

    except requests.exceptions.HTTPError as http_err:
        print(f"GPT API HTTP 錯誤: {http_err}")
        return JsonResponse({"error": f"GPT API 錯誤: {http_err.response.text}"}, status=http_err.response.status_code)
    except Exception as e:
        print(traceback.format_exc())
        return JsonResponse({"error": str(e)}, status=500)