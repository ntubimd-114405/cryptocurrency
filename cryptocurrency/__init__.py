from __future__ import absolute_import, unicode_literals

# 這樣 Django 启动時會自動加載 Celery 配置
from .celery import app as celery_app

__all__ = ('celery_app',)