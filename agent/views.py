from django.shortcuts import render

# agent/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import UserProfile

@login_required
def user_questionnaire(request):
    if request.method == 'POST':
        risk_type = request.POST['risk_type']
        investment_goal = request.POST['investment_goal']
        total_budget = request.POST['total_budget']
        tolerance = request.POST['tolerance_per_coin']

        profile, created = UserProfile.objects.update_or_create(
            user=request.user,
            defaults={
                'risk_type': risk_type,
                'investment_goal': investment_goal,
                'total_budget': total_budget,
                'tolerance_per_coin': tolerance,
            }
        )
        return redirect('asset_suggestion')

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
