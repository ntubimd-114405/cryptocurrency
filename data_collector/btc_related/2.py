import requests

def stats_api():
    url="https://api.blockchain.info/stats"
    response = requests.get(url)
    data = response.json()
    return data


def pools_api():#https://www.blockchain.com/explorer/api/charts_api
    url="https://api.blockchain.info/pools?timespan=1hour"
    response = requests.get(url)
    data = response.json()
    return data


if __name__ == "__main__":
    print(stats_api())
    print(pools_api())