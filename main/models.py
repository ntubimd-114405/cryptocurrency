from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class Coin(models.Model):
    coinname = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=100)  # 假設這是加密貨幣的簡稱
    logo_url = models.URLField(blank=True, null=True)
    api_id = models.BigIntegerField( unique=True, null=True)

    def __str__(self):
        return self.coinname

class BitcoinPrice(models.Model):
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    usd = models.FloatField()
    twd = models.FloatField()
    jpy = models.FloatField()
    eur = models.FloatField()
    market_cap = models.DecimalField(max_digits=30, decimal_places=2, null=True)  # 市值
    volume_24h = models.DecimalField(max_digits=30, decimal_places=2, null=True)  # 24小時交易量
    change_24h = models.DecimalField(max_digits=5, decimal_places=2, null=True)  # 24小時變動百分比
    timestamp = models.DateTimeField()

    def __str__(self):
        return f"{self.coin.coinname} - {self.timestamp}"
    
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_image = models.ImageField(upload_to='profile_images/', default='default/default.jpg', null=True)
    favorite_coin = models.ManyToManyField(Coin, blank=True)

    def __str__(self):
        return self.user.username



@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class NewsWebsite(models.Model):
    name = models.CharField(max_length=255)  # 新聞網站名稱
    url = models.URLField(max_length=255, unique=True)
    icon_url = models.URLField(max_length=500)

    def __str__(self):
        return self.name


class NewsArticle(models.Model):
    title = models.CharField(max_length=255, null=True)  # 標題
    url = models.URLField(max_length=255,unique=True)  # 網址
    image_url = models.URLField(null=True,max_length=500)  # 圖片網址
    content = models.TextField(null=True)  # 內文欄位，使用 TextField 儲存長篇文字內容
    time = models.DateTimeField(null=True)
    website = models.ForeignKey(NewsWebsite, on_delete=models.CASCADE)  # 外鍵關聯到新聞網站

    SENTIMENT_CHOICES = [
        ('positive', 'Positive'),
        ('neutral', 'Neutral'),
        ('negative', 'Negative'),
    ]

    sentiment = models.CharField(
        max_length=10,
        choices=SENTIMENT_CHOICES,
        null=True,  # 允許存入 NULL 值
        blank=True  # 表單驗證時允許為空
    )

    def __str__(self):
        return self.title
    
    
class CoinHistory(models.Model):
    coin = models.ForeignKey(Coin, related_name='history', on_delete=models.CASCADE)  # 外鍵，關聯到 Coin 模型
    date = models.DateTimeField(db_index=True)  # 日期
    open_price = models.DecimalField(max_digits=20, decimal_places=10)  # 開盤價
    high_price = models.DecimalField(max_digits=20, decimal_places=10)  # 最高價
    low_price = models.DecimalField(max_digits=20, decimal_places=10)  # 最低價
    close_price = models.DecimalField(max_digits=20, decimal_places=10)  # 收盤價
    volume = models.DecimalField(max_digits=65, decimal_places=10)  # 成交量

    class Meta:
        # 如果你希望能快速按時間範圍進行查詢，這裡可以加上索引
        indexes = [
            models.Index(fields=['coin', 'date']),  # 這個索引有助於按 Coin 和日期篩選和排序
        ]
        # 可選：你可以加一個排序，使得查詢這個模型時會自動按日期倒序排列
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.coin.coinname} - {self.date.strftime('%Y-%m-%d %H:%M:%S')}"
    

class XPost(models.Model):
    ids = models.CharField(max_length=255, unique=True)
    html = models.TextField()
    text = models.TextField()

    def __str__(self):
        return f"Tweet ID: {self.ids}"
    
class UserNotificationPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="notification_preference")
    news_notifications = models.BooleanField(default=True)  # 是否接收新聞通知
    email_notifications = models.BooleanField(default=False)  # 電子郵件通知
    site_notifications = models.BooleanField(default=True)  # 站內通知

class DepthData(models.Model):
    coin = models.ForeignKey(Coin, related_name='depth_data', on_delete=models.CASCADE)  # 外鍵，關聯到 Coin 模型
    last_update_id = models.BigIntegerField()
    bids = models.JSONField()  # 使用 JSONField 來存儲 bids
    asks = models.JSONField()  # 使用 JSONField 來存儲 asks
    created_at = models.DateTimeField(auto_now_add=True)  # 儲存資料創建的時間

    def __str__(self):
        return f"Last Update ID: {self.last_update_id}"
    

