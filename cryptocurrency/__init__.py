from __future__ import absolute_import, unicode_literals
# 這是Celery的初始化
from .celery import app as celery_app

__all__ = ('celery_app',)