from django.db import models
from main.models import Coin  # 引入 Coin 模型

class TrendData(models.Model):
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE, related_name='trend_data')
    date = models.DateTimeField(help_text="資料時間，採用 UTC 時區")
    full_value = models.IntegerField(help_text="名稱流量數量")  # 儲存搜尋量指數（名稱流量）
    abbreviated_value = models.IntegerField(help_text="簡稱流量數量")  # 儲存搜尋量指數（簡稱流量）

    def __str__(self):
        return f"{self.coin.coinname} @ {self.date}: {self.full_value}, {self.abbreviated_value}"


class FinancialSymbol(models.Model):
    symbol = models.CharField(max_length=10, unique=True)  # 股票或指數的符號
    name = models.CharField(max_length=100)                # 金融工具的名稱

    def __str__(self):
        return self.name

class FinancialData(models.Model):
    symbol = models.ForeignKey(FinancialSymbol, on_delete=models.CASCADE, related_name='financial_data')  # 與 FinancialSymbol 之間的關聯
    date = models.DateField()                              # 日期
    open_price = models.FloatField()                       # 開盤價
    high_price = models.FloatField()                       # 最高價
    low_price = models.FloatField()                        # 最低價
    close_price = models.FloatField()                      # 收盤價
    volume = models.BigIntegerField()                      # 交易量

    class Meta:
        unique_together = ('symbol', 'date')               # 確保同一日期下的數據唯一
        ordering = ['date']                                 # 按日期排序

    def __str__(self):
        return f"{self.symbol.symbol} on {self.date}"
    

class Indicator(models.Model):
    name = models.CharField(max_length=255, unique=True)  # 指标名称，唯一性约束
    abbreviation = models.CharField(max_length=255, unique=True,null=True,blank=True)  # 可选的描述字段

    def __str__(self):
        return self.name
    
class IndicatorValue(models.Model):
    indicator = models.ForeignKey(Indicator, on_delete=models.CASCADE)  # 外键关联到 Indicator 表
    date = models.DateField()  # 日期
    value = models.FloatField()  # 指标值

    def __str__(self):
        return f"{self.indicator.name} - {self.date} - {self.value}"
    
class BitcoinMetric(models.Model):
    name = models.CharField(max_length=100, unique=True)
    unit = models.CharField(max_length=50, blank=True, null=True)
    period = models.CharField(max_length=20, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class BitcoinMetricData(models.Model):
    metric = models.ForeignKey(BitcoinMetric, on_delete=models.CASCADE, related_name="data")
    date = models.DateTimeField()
    value = models.FloatField()

    class Meta:
        unique_together = ('metric', 'date')  # 避免同一時間重複資料

    def __str__(self):
        return f"{self.metric.name} - {self.timestamp}: {self.value}"
