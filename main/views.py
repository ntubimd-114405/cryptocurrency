from django.shortcuts import render, get_object_or_404,redirect
import requests
from django.http import JsonResponse,HttpResponseRedirect
from .models import BitcoinPrice,UserProfile,Coin,CoinHistory,User
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
import re

def home(request):
    try:
        user = request.user
        today = timezone.now().date()

        # 取得該使用者的簽到資料（如果沒有就不傳）
        sign_in_record = SignIn.objects.filter(user=user).first()

        progress_percentage = 0
        if sign_in_record:
            progress_days = sign_in_record.consecutive_sign_in_count % 7
            progress_percentage = int((progress_days / 7) * 100)

            # 特別處理剛好 7 的情況
            if progress_days == 0 and sign_in_record.consecutive_sign_in_count > 0:
                progress_percentage = 100

        # 取得資料庫中的所有價格，按 id 升序排列
        top_coins = BitcoinPrice.objects.all().order_by('id')[:5]
        increase_coins = BitcoinPrice.objects.all().order_by('-change_24h')[:5]
        decline_coins = BitcoinPrice.objects.all().order_by('change_24h')[:5]
        volume = BitcoinPrice.objects.all().order_by('-volume_24h')[:10]
        image_url = request.build_absolute_uri(static('images/crypto.png')) 
        
        # 渲染到模板
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

    if not start_str or not end_str:
        return JsonResponse({'error': '缺少 start 或 end 參數'}, status=400)

    start = parse_datetime(start_str)
    end = parse_datetime(end_str)

    if not start or not end:
        return JsonResponse({'error': 'start 或 end 參數格式錯誤'}, status=400)

    if start >= end:
        return JsonResponse({'error': 'start 需早於 end'}, status=400)

    # 查詢資料，注意這裡假設 date 存的是 UTC 時間
    qs = CoinHistory.objects.filter(
        coin_id=coin_id,
        date__gte=start,
        date__lte=end
    ).order_by('date')

    data = []
    for item in qs:
        # amCharts 需要 timestamp (毫秒)
        timestamp = int(item.date.timestamp() * 1000)
        data.append({
            "date": timestamp,
            "open": float(item.open_price),
            "high": float(item.high_price),
            "low": float(item.low_price),
            "close": float(item.close_price),
            "volume": float(item.volume)
        })

    return JsonResponse({"data": data})

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


from data_analysis.text_generation.api import finance_LLM_api
@csrf_exempt
def chat_api(request):
    if request.method == "POST":
        data = json.loads(request.body)
        text = data.get("text", "")
        print(text)
        response = finance_LLM_api(text)
        print(response)
        return JsonResponse({"response": response})
    return JsonResponse({"error": "Invalid request"}, status=400)

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
