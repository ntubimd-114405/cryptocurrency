# crypto_ai_agent/price_agent.py

from datetime import timedelta
from django.utils.timezone import now
from main.models import Coin, CoinHistory

def run_price_agent(days: int = 30) -> str:
    end_time = now()
    start_time = end_time - timedelta(days=days)
    coins = Coin.objects.all()
    outputs = []
    for coin in coins:
        history = CoinHistory.objects.filter(coin=coin, date__range=(start_time, end_time)).order_by("date")
        if not history.exists():
            continue
        latest = history.last()
        outputs.append(f"{coin.coinname}（{coin.abbreviation}）最新收盤價為 {latest.close_price}（{latest.date.date()}）")
    return "\n".join(outputs)
