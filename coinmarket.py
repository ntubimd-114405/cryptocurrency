#幣種分類
import os
import requests
import django
import time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cryptocurrency.settings")
django.setup()

from main.models import Coin, CoinCategory, CoinCategoryRelation

API_KEY = os.getenv("coinmarketcap_api")

import re

CATEGORY_RULES = {
    "主流幣": ["Bitcoin Ecosystem", "Layer 1", "Binance Ecosystem", "Ethereum Ecosystem", "Solana Ecosystem", "Avalanche Ecosystem", "Polygon Ecosystem", "Cardano Ecosystem", "BNB Chain Ecosystem", "Polkadot Ecosystem"],
    "穩定幣": ["Stablecoin", "Fiat Stablecoin", "USD Stablecoin", "EUR Stablecoin", "Algorithmic Stablecoin"],
    "迷因幣": ["Meme", "Animal Memes", "Political Memes", "Celebrity Memes", "Four.Meme Ecosystem", "IP Memes"],
    "成長幣": ["DeFi", "Smart Contracts", "Decentralized Exchange (DEX) Token", "Lending & Borrowing", "Yield Farming", "Yield Aggregator", "Layer 2", "Rollups", "Scaling", "Oracles"],
}

def normalize_tag(s):
    # 轉小寫，去除非字母數字
    s = s.lower()
    s = re.sub(r'[^a-z0-9]', '', s)
    return s

def classify_by_tags(tags):
    normalized_tags = [normalize_tag(t) for t in tags]
    matched = set()
    for cat, keywords in CATEGORY_RULES.items():
        for kw in keywords:
            norm_kw = normalize_tag(kw)
            if norm_kw in normalized_tags:
                matched.add(cat)
                # print(f"匹配到分類: {cat}，關鍵字: {kw}")
    if not matched:
        matched.add("其他")
    return matched



def classify_coin(api_id):
    url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/info?id={api_id}"
    headers = {"X-CMC_PRO_API_KEY": API_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        coin_data = data.get("data", {}).get(str(api_id), {})
        tags = coin_data.get("tags", [])
        matched_cats = classify_by_tags(tags)
        return list(matched_cats)
    except Exception as e:
        print(f"CMC API 失敗 id={api_id}：{e}")
        return ["其他"]


def update_all_coin_categories():
    coins = Coin.objects.all()[:50]  
    updated_count = 0
    for coin in coins:
        if not coin.api_id:
            print(f"{coin.coinname} 沒有設定 api_id，跳過")
            continue

        cats = classify_coin(coin.api_id)

        # 清除該幣種舊有的分類關聯
        CoinCategoryRelation.objects.filter(coin=coin).delete()

        # 新增新的分類關聯
        for cat_name in cats:
            cat_obj, created = CoinCategory.objects.get_or_create(name=cat_name)
            CoinCategoryRelation.objects.create(coin=coin, category=cat_obj)

        print(f"{coin.coinname} 分類為：{', '.join(cats)}")
        updated_count += 1

        time.sleep(0.5)  # 延遲1秒，視API限制可調整

    print(f"共更新 {updated_count} 筆幣種分類")

if __name__ == "__main__":
    if not API_KEY:
        print("請先設定環境變數 coinmarketcap_api")
    else:
        update_all_coin_categories()
