from django.db import models
from django.contrib.auth.models import User

class DataLocation(models.Model):
    # 與 User 模型建立外鍵關聯，代表一個 User 可以擁有多個 DataLocation
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="data_locations")
    
    name = models.CharField(max_length=255, help_text="模型名稱")

    status = models.CharField(max_length=50 , default="wait")

    # 儲存時間戳記，代表資料創建的時間
    created_at = models.DateTimeField(auto_now_add=True, help_text="資料節位置創建時間")

    def __str__(self):
        return f"{self.name} - {self.user.username}"
