# administrator/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.db.models import Q  

from main.models import Coin

# ✅ 只允許 superuser 進入
from django.contrib.auth.decorators import user_passes_test

def superuser_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)


# ============================
# 後台 Dashboard
# ============================
@superuser_required
def dashboard(request):
    return render(request, 'administrator/dashboard.html')


# ============================
# 幣種管理
# ============================
@superuser_required
def crypto_management(request):
    query = request.GET.get('q', '')  # 預設是空字串，不會出現 None
    coins = Coin.objects.all()

    if query:
        coins = coins.filter(
            Q(coinname__icontains=query) |
            Q(abbreviation__icontains=query)
        )

    return render(request, 'administrator/crypto_management.html', {
        'coins': coins,
        'query': query
    })


@superuser_required
def edit_crypto(request, id):
    coin = get_object_or_404(Coin, id=id)
    
    if request.method == 'POST':
        coin.coinname = request.POST.get('coinname')
        coin.abbreviation = request.POST.get('abbreviation')
        coin.logo_url = request.POST.get('logo_url')
        coin.api_id = request.POST.get('api_id')
        coin.save()
        
        return HttpResponseRedirect(reverse('administrator:crypto_management'))
    
    return render(request, 'administrator/edit_crypto.html', {'coin': coin})


@superuser_required
def delete_crypto(request, id):
    coin = get_object_or_404(Coin, id=id)
    
    if request.method == 'POST':
        coin.delete()
        return redirect('administrator:crypto_management')

    return render(request, 'administrator/delete_crypto_confirm.html', {'coin': coin})


# ============================
# 使用者管理
# ============================
@superuser_required
def user_management(request):
    query = request.GET.get('q', '')  
    users = User.objects.select_related('profile')

    if query:
        users = users.filter(username__icontains=query) | users.filter(email__icontains=query)

    return render(request, 'administrator/user_management.html', {'users': users, 'query': query})


@superuser_required
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
