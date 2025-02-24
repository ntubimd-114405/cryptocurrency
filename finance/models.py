from django.db import models

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
