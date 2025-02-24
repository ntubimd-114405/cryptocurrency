import requests
#目前沒打算使用，因為沒有歷史數據
#https://www.blockchain.com/explorer/api/charts_api
def stats_api():
    url="https://api.blockchain.info/stats"
    response = requests.get(url)
    data = response.json()
    return data


def pools_api():
    url="https://api.blockchain.info/pools?timespan=1hour"
    response = requests.get(url)
    data = response.json()
    return data


if __name__ == "__main__":
    print(stats_api())
    print(pools_api())