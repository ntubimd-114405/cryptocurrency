from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# 設定 Django 的默認設置模塊
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cryptocurrency.settings')

app = Celery('cryptocurrency')

# 使用 RabbitMQ 作為消息代理
app.config_from_object('django.conf:settings', namespace='CELERY')

# 發現並自動加載所有註冊的 Django 任務
app.autodiscover_tasks()

app.conf.update(
    task_default_queue='default',
    task_queues={'default': {'exchange': 'default', 'routing_key': 'default'}},
    worker_concurrency=1,  # 設定單線程工作
    worker_pool='solo',  # 使用 solo 池
)
