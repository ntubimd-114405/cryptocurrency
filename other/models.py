from django.db import models
from main.models import Coin  # 引入 Coin 模型

class TrendData(models.Model):
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE, related_name='trend_data')
    date = models.DateTimeField(help_text="資料時間，採用 UTC 時區")
    full_value = models.IntegerField(help_text="名稱流量數量")  # 儲存搜尋量指數（名稱流量）
    abbreviated_value = models.IntegerField(help_text="簡稱流量數量")  # 儲存搜尋量指數（簡稱流量）

    def __str__(self):
        return f"{self.coin.coinname} @ {self.date}: {self.full_value}, {self.abbreviated_value}"
