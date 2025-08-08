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
    change_24h = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 24小時變動百分比
    timestamp = models.DateTimeField()

    def __str__(self):
        return f"{self.coin.coinname} - {self.timestamp}"
    
class CoinCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class CoinCategoryRelation(models.Model):
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    category = models.ForeignKey(CoinCategory, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.coin.abbreviation} - {self.category.name}"

    
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_image = models.ImageField(upload_to='profile_images/', default='default/default.jpg', null=True)
    favorite_coin = models.ManyToManyField(Coin, blank=True)
    MEMBERSHIP_CHOICES = [
        ('free', 'Free'),
        ('premium', 'Premium'),
    ]
    membership = models.CharField(max_length=10, choices=MEMBERSHIP_CHOICES, default='free')

    def __str__(self):
        return self.user.username



@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
    
    
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
    

class SignIn(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    last_sign_in_date = models.DateField(null=True, blank=True)
    sign_in_count = models.PositiveIntegerField(default=0)
    consecutive_sign_in_count = models.PositiveIntegerField(default=0)  # 新增字段

    def __str__(self):
        return f'{self.user.username} SignIn'

    def update_consecutive_sign_in(self):
        # 判断今天是否是连续签到的一天
        today = timezone.now().date()
        if self.last_sign_in_date == today - timezone.timedelta(days=1):
            self.consecutive_sign_in_count += 1
        else:
            self.consecutive_sign_in_count = 1  # 重置连续签到为1
        self.save()

# 題目類型選項
QUESTION_TYPES = [
    ('text', '開放填答'),
    ('radio', '單選'),
    ('checkbox', '複選'),
    ('rating', '滿意度'),
    ('select', '下拉選單'),
]

class FeedbackQuestion(models.Model):
    text = models.CharField(max_length=255)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='text')
    required = models.BooleanField(default=True)

    def __str__(self):
        return self.text

class FeedbackOption(models.Model):
    question = models.ForeignKey(FeedbackQuestion, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.question.text} - {self.text}"

class FeedbackAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="使用者")
    question = models.ForeignKey(FeedbackQuestion, on_delete=models.CASCADE)
    answer_text = models.TextField()  # 儲存使用者選的選項或文字
    submitted_at = models.DateTimeField(auto_now_add=True)

class PageTracker(models.Model):
    page_name = models.CharField(max_length=100, unique=True)
    impressions = models.IntegerField(default=0)