# crypto_ai_agent/price_data.py
#還未使用
from datetime import timedelta
from main.models import Coin, CoinHistory
import matplotlib.pyplot as plt
import io
import base64
from django.utils.timezone import now

def get_coin_price_summary(days: int = 30):
    end_time = now()
    start_time = end_time - timedelta(days=days)

    coins = Coin.objects.all()
    result = []

    for coin in coins:
        history = CoinHistory.objects.filter(
            coin=coin, date__range=(start_time, end_time)
        ).order_by("date")

        if not history.exists():
            continue

        prices = [float(h.close_price) for h in history]
        dates = [h.date.strftime("%Y-%m-%d") for h in history]

        img_base64 = plot_price_chart(dates, prices, coin.coinname)
        result.append({
            "coin": coin.coinname,
            "abbreviation": coin.abbreviation,
            "logo_url": coin.logo_url,
            "chart_base64": img_base64,
        })

    return result

def plot_price_chart(dates, prices, title=""):
    plt.figure(figsize=(6, 3))
    plt.plot(dates, prices, label="收盤價", color="green")
    plt.xticks(rotation=45)
    plt.title(f"{title} 價格走勢")
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    return img_base64
