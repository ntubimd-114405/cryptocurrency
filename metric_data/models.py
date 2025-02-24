from django.db import models

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
