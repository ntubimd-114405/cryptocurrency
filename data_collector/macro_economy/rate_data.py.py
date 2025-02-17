import requests

def get_exchange_rate(base_currency='USD'):#可以加映射表
    url = f'https://api.exchangerate-api.com/v4/latest/{base_currency}'
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print(data)


# 使用範例
if __name__ == "__main__":
    get_exchange_rate('USD')  # 以美元為基準貨幣
