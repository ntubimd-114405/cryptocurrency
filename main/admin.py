from django.contrib import admin
from .models import Coin, BitcoinPrice, UserProfile, NewsWebsite, NewsArticle, CoinHistory, XPost
from django.utils.html import format_html

@admin.register(Coin)
class CoinAdmin(admin.ModelAdmin):
    list_display = ('coinname', 'abbreviation', 'logo_url', 'api_id', 'show_logo')

    def show_logo(self, obj):
        return format_html('<img src="{}" style="height: 40px;"/>', obj.logo_url)

@admin.register(BitcoinPrice)
class BitcoinPriceAdmin(admin.ModelAdmin):
    list_display = ('coin', 'usd', 'twd', 'jpy', 'eur', 'market_cap', 'volume_24h', 'change_24h', 'timestamp')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'avatar_image', 'get_favorite_coins')

    def get_favorite_coins(self, obj):
        return ", ".join([coin.coinname for coin in obj.favorite_coin.all()])
    get_favorite_coins.short_description = 'Favorite Coins'

    def avatar_image(self, obj):
        # 確保顯示圖片，而不是圖片的 URL
        return format_html('<img src="{}" style="height: 40px;"/>'.format(obj.profile_image.url))

    avatar_image.short_description = 'Avatar'  # 設置顯示的欄位名稱






@admin.register(NewsWebsite)
class NewsWebsiteAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon_url')

@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'image_url', 'time', 'website')

@admin.register(CoinHistory)
class CoinHistoryAdmin(admin.ModelAdmin):
    list_display = ('coin', 'date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume')

@admin.register(XPost)
class XPostAdmin(admin.ModelAdmin):
    list_display = ('ids', 'html', 'text')
