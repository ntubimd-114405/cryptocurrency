from django.db import models

# agent/models.py
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    RISK_CHOICES = [
        ('保守型', '保守型'),
        ('中性型', '中性型'),
        ('積極型', '積極型'),
    ]

    INVESTMENT_GOAL_CHOICES = [
        ('短期獲利', '短期獲利'),
        ('長期增值', '長期增值'),
        ('資產保值', '資產保值'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    risk_type = models.CharField(max_length=10, choices=RISK_CHOICES)
    investment_goal = models.CharField(max_length=10, choices=INVESTMENT_GOAL_CHOICES)
    total_budget = models.DecimalField(max_digits=12, decimal_places=2)
    tolerance_per_coin = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} 的風險屬性"
