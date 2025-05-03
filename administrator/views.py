# administrator/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password


@login_required
def dashboard(request):
    return render(request, 'administrator/dashboard.html')

from main.models import Coin
from django.contrib.auth.decorators import login_required

@login_required
def crypto_management(request):
    coins = Coin.objects.all()
    return render(request, 'administrator/crypto_management.html', {'coins': coins})


from django.http import HttpResponseRedirect
from django.urls import reverse

def edit_crypto(request, id):
    coin = get_object_or_404(Coin, id=id)
    
    if request.method == 'POST':
        # 處理更新邏輯
        coin.coinname = request.POST.get('coinname')
        coin.abbreviation = request.POST.get('abbreviation')
        coin.logo_url = request.POST.get('logo_url')
        coin.api_id = request.POST.get('api_id')
        coin.save()
        
        return HttpResponseRedirect(reverse('administrator:crypto_management'))  # 重定向回幣種管理頁面
    
    return render(request, 'administrator/edit_crypto.html', {'coin': coin})


def delete_crypto(request, id):
    # 確認幣種是否存在
    coin = get_object_or_404(Coin, id=id)
    
    if request.method == 'POST':
        # 刪除幣種
        coin.delete()
        return redirect('administrator:crypto_management')  # 重定向到幣種管理頁面

    return render(request, 'administrator/delete_crypto_confirm.html', {'coin': coin})




from django.contrib.auth.decorators import user_passes_test

def is_superuser(user):
    return user.is_superuser

@user_passes_test(is_superuser)
def user_management(request):
    query = request.GET.get('q', '')  # 取得搜尋關鍵字
    users = User.objects.select_related('profile')

    if query:
        users = users.filter(username__icontains=query) | users.filter(email__icontains=query)

    return render(request, 'administrator/user_management.html', {'users': users, 'query': query})

def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        membership = request.POST.get("membership")
        is_active = request.POST.get("is_active") == "1"
        new_password = request.POST.get("password")

        # 更新基本欄位
        user.username = username
        user.email = email
        user.is_active = is_active

        if new_password:
            user.password = make_password(new_password)

        user.save()

        # 更新 Profile
        user.profile.membership = membership
        user.profile.save()

        return redirect("administrator:user_management")

    return render(request, "administrator/edit_user.html", {"user": user})

