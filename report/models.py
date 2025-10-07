from django.db import models
from django.contrib.auth.models import User

class WeeklyReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    year = models.IntegerField()
    week = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    summary = models.TextField(null=True, blank=True)
    news_summary = models.TextField(null=True, blank=True)
    word_frequencies = models.JSONField(null=True, blank=True)
    ma20_data = models.JSONField(null=True, blank=True)
    ma60_data = models.JSONField(null=True, blank=True)
    ohlc_data = models.JSONField(null=True, blank=True)
    rsi_data = models.JSONField(null=True, blank=True)
    macd_data = models.JSONField(null=True, blank=True)
    macd_signal_data = models.JSONField(null=True, blank=True)
    coin_analysis = models.TextField(null=True, blank=True)
    financial_data_json = models.JSONField(null=True, blank=True)
    indicator_data_json = models.JSONField(null=True, blank=True)
    bitcoin_data_json = models.JSONField(null=True, blank=True)
    long_term_analysis = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'year', 'week')

    def __str__(self):
        return f'{self.user.username} - {self.year} W{self.week}'

