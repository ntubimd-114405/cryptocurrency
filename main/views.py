from django.shortcuts import render, get_object_or_404,redirect
import requests
from django.http import JsonResponse,HttpResponseRedirect
from .models import BitcoinPrice,UserProfile,Coin,NewsWebsite,NewsArticle,CoinHistory,User
from datetime import datetime
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
import re
 
def home(request):
    try:
        # 取得資料庫中的所有價格，按 id 升序排列
        all_prices = BitcoinPrice.objects.all().order_by('id')

        # 渲染到模板
        return render(request, 'home.html', {
            'all_prices': all_prices,
        })

    except Exception as e:
        print(f"錯誤: {e}")
        return render(request, 'home.html', {
            'error': '無法獲取資料，請稍後再試。'
        })



def crypto_detail(request, pk):
    # 查詢 CoinHistory 資料
    coin_history = CoinHistory.objects.filter(coin_id=pk).order_by('date')

    # 準備資料
    dates = [entry.date for entry in coin_history]
    open_prices = [entry.open_price for entry in coin_history]
    high_prices = [entry.high_price for entry in coin_history]
    low_prices = [entry.low_price for entry in coin_history]
    close_prices = [entry.close_price for entry in coin_history]

    # 創建 K 線圖
    fig = go.Figure(data=[go.Candlestick(
        x=dates,
        open=open_prices,
        high=high_prices,
        low=low_prices,
        close=close_prices,
        name="Candlestick"
    )])

    # 更新圖表的布局
    fig.update_layout(
        title=f"Price History for Coin {pk}",
        xaxis_title="Date",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False
    )

    # 將圖表的 HTML 代碼傳遞到模板
    graph = fig.to_html(full_html=False)
    price = get_object_or_404(BitcoinPrice, pk=pk)  # 獲取單一對象，若不存在則返回404
    return render(request, 'crypto_detail.html', {'price':price,'graph': graph})

def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')

        # 檢查郵箱是否已經註冊
        if User.objects.filter(email=email).exists():
            messages.error(request, '這個email已經被使用')
            return render(request, 'register.html')  # 若郵箱已被使用，返回註冊頁面

        try:
            # 使用 create_user 方法來創建用戶，這會自動加密密碼
            user = User.objects.create_user(
                username=username,
                password=password,  # 這裡傳遞原始密碼即可
                email=email,
                first_name=first_name,
                last_name=last_name
            )
            user.save()

            # 註冊成功後跳轉到 'login' 頁面
            messages.success(request, 'Your account has been created! Please log in.')
            return redirect('login')

        except Exception as e:
            messages.error(request, f'Error creating user: {e}')
            return render(request, 'register.html')  # 出現錯誤時返回註冊頁面

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
            return render(request, 'login.html', {'error': 'Invalid username or password'})
    return render(request, 'login.html')

# 登出功能
def logout_view(request):
    logout(request)
    return redirect('home')  # 登出後跳轉到登入頁

from django.db.models import F
from django.core.paginator import Paginator
from django.shortcuts import render

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
    # "default" 狀態下不進行排序，保持自然順序

    paginator = Paginator(all_prices, 10)  # 每頁顯示10條數據
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
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
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model

class CustomPasswordResetView(auth_views.PasswordResetView):
    template_name = 'password_reset_form.html'  # 忘記密碼表單
    email_template_name = 'password_reset_email.html'  # 發送郵件的模板
    success_url = reverse_lazy('password_reset_done')  # 成功後跳轉到 `password_reset_done`

class CustomPasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = 'password_reset_done.html'  # 提示郵件已發送的頁面

class CustomPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = 'password_reset_confirm.html'  # 用戶輸入新密碼的頁面
    success_url = reverse_lazy('password_reset_complete')  # 成功設置新密碼後跳轉的頁面

class CustomPasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = 'password_reset_complete.html'  # 密碼重設完成後的頁面

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


from django.shortcuts import render
from .models import CoinHistory
from django.http import JsonResponse

def crypto_detail(request, coin_id):
    data = Coin.objects.get(id=coin_id)
    return render(request, 'crypto_detail.html', {'coin_id': coin_id,'data':data})

from django.db.models import Min, Max, Sum, Subquery, OuterRef
from django.db.models.functions import TruncMinute, TruncHour, TruncDay, TruncWeek, TruncMonth
from django.http import JsonResponse
from .models import CoinHistory

def coin_history(request, coin_id):
    # 獲取請求參數，並設置預設值
    end = int(request.GET.get('start', 0))  # 默認從第0條數據開始
    limit = int(request.GET.get('limit', 1000))  # 默認最多返回 1000 條數據
    timeframe = request.GET.get('timeframe', 'minute')  # 默認為分鐘級別
    total_count = CoinHistory.objects.filter(coin_id=coin_id).count()
    # 計算 start 位置
    end = int(total_count * (end / 100))  # 轉換為數據索引位置
    
    # 時間聚合對應關係
    time_mapping = {
        'minute': TruncMinute('date'),
        'hour': TruncHour('date'),
        'day': TruncDay('date'),
        'week': TruncWeek('date'),
        'month': TruncMonth('date'),
    }

    time_trunc = time_mapping[timeframe]

    # 查詢並聚合數據
    history_data = CoinHistory.objects.filter(coin_id=coin_id) \
    .values('date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume') \
    .order_by('date')[max(0, end-limit):end]  # 按日期升序排列
    # 轉換為列表

    data = list(history_data)
    return JsonResponse({'data': data, 'total_count': total_count}, safe=False)