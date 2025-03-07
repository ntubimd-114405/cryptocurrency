from django.db import models


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
        return self.title