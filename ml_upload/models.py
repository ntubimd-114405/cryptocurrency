from django.db import models
from django.contrib.auth.models import User

class DataLocation(models.Model):
    # 與 User 模型建立外鍵關聯，代表一個 User 可以擁有多個 DataLocation
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="data_locations")
    
    # 存儲資料節位置的字段，可以是文字、URL 或路徑
    location = models.CharField(max_length=255, help_text="儲存資料位置的路徑或 URL")

    # 可選：可以為資料節位置添加一些額外的描述字段
    description = models.TextField(null=True, blank=True, help_text="資料節位置的描述")

    # 儲存時間戳記，代表資料創建的時間
    created_at = models.DateTimeField(auto_now_add=True, help_text="資料節位置創建時間")

    def __str__(self):
        return f"{self.location} - {self.user.username}"
