from django.db import models

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