import requests

urls=[
    "https://api.blockchain.info/charts/hash-rate?timespan=30days&format=json",
    "https://api.blockchain.info/charts/hash-rate?timespan=30days&unit=hours&format=json",
    "https://api.blockchain.info/charts/n-transactions?timespan=30days&format=json",
    "https://api.blockchain.info/charts/avg-block-size?timespan=30days&format=json"
]

for i in urls:
    try:
        response = requests.get(i)
        data = response.json()
        print(data)
    except:
        print(None)