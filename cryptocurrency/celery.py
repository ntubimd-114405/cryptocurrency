from __future__ import absolute_import, unicode_literals
import django


import os
from celery import Celery
from django.conf import settings

# 设置 Django 配置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cryptocurrency.settings')

# 确保 Django 已经初始化
django.setup()

app = Celery('cryptocurrency')

# 配置 Celery 使用 Django 设置
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现任务
app.autodiscover_tasks()
