from django.db import models
from django.contrib.auth.models import User

class WeeklyReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    year = models.IntegerField()
    week = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    summary = models.TextField()
    news_summary = models.TextField()
    word_frequencies = models.JSONField()
    ma20_data = models.JSONField()
    ma60_data = models.JSONField()
    ohlc_data = models.JSONField()
    rsi_data = models.JSONField()
    macd_data = models.JSONField()
    macd_signal_data = models.JSONField()
    coin_analysis = models.TextField()
    financial_data_json = models.JSONField(null=True)
    indicator_data_json = models.JSONField(null=True)
    bitcoin_data_json = models.JSONField(null=True)
    long_term_analysis = models.TextField(null=True)

    class Meta:
        unique_together = ('user', 'year', 'week')

    def __str__(self):
        return f'{self.user.username} - {self.year} W{self.week}'

