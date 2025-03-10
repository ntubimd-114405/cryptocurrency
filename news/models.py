from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Website(models.Model):
    name = models.CharField(max_length=255)  # 新聞網站名稱
    url = models.URLField(max_length=255, unique=True)
    icon_url = models.URLField(max_length=500)

    def __str__(self):
        return self.name


class Article(models.Model):
    title = models.CharField(max_length=255, null=True)  # 標題
    url = models.URLField(max_length=255,unique=True)  # 網址
    image_url = models.URLField(null=True,max_length=500)  # 圖片網址
    content = models.TextField(null=True)  # 內文欄位，使用 TextField 儲存長篇文字內容
    summary = models.TextField(null=True)  # 簡短摘要
    time = models.DateTimeField(null=True)
    website = models.ForeignKey(Website, on_delete=models.CASCADE)  # 外鍵關聯到新聞網站

    def __str__(self):
        return self.title if self.title else "No Title"
    

class Comment(models.Model):
    # 外鍵關聯到新聞文章
    article = models.ForeignKey(Article, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)# 可選：可以使用匿名評論
    content = models.TextField()# 評論內容
    created_at = models.DateTimeField(default=timezone.now)# 創建時間
    updated_at = models.DateTimeField(auto_now=True)# 更新時間

    def __str__(self):
        return f'Comment by {self.user.username} on {self.article.title}'

class Reply(models.Model):
    comment = models.ForeignKey(Comment, related_name='replies', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Reply by {self.user.username} to comment {self.comment.id}'
    
class XPost(models.Model):
    ids = models.CharField(max_length=255, unique=True)
    html = models.TextField()
    text = models.TextField()

    def __str__(self):
        return f"Tweet ID: {self.ids}"