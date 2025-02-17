import requests
'''
https://api.blockchain.info/charts/$chartName?timespan=$timespan&rollingAverage=$rollingAverage&start=$start&format=$format&sampled=$sampled
$timespan- Duration of the chart, default is 1 year for most charts, 1 week for mempool charts. (Optional)
$rollingAverage- Duration over which the data should be averaged. (Optional)
$start- Datetime at which to start the chart. (Optional)
$format- Either JSON or CSV, defaults to JSON. (Optional)
$sampled- Boolean set to 'true' or 'false' (default 'true'). If true, limits the number of datapoints returned to ~1.5k for performance reasons. (Optional)
https://api.blockchain.info/charts/transactions-per-second?timespan=5weeks&rollingAverage=8hours&format=json
'''

def get_bitcoin_hashrate():
    url = "https://api.blockchain.info/charts/hash-rate?timespan=1days&format=json"
    response = requests.get(url)
    data = response.json()
    return data

def get_bitcoin_difficulty():
    url = "https://api.blockchain.info/q/getdifficulty"
    response = requests.get(url)
    data = response.json()
    return data

def get_bitcoin_active_addresses():
    url = "https://api.blockchain.info/charts/n-unique-addresses?timespan=1days&format=json"
    response = requests.get(url)
    data = response.json()
    return data

def get_bitcoin_block_height():
    url = "https://api.blockchain.info/q/getblockcount"
    response = requests.get(url)
    data = response.text
    return data

def get_bitcoin_block_size():
    url = "https://api.blockchain.info/charts/avg-block-size?timespan=1days&format=json"
    response = requests.get(url)
    data = response.json()
    return data

def main():
    hashrate = get_bitcoin_hashrate()
    difficulty = get_bitcoin_difficulty()
    active_addresses = get_bitcoin_active_addresses()
    block_height = get_bitcoin_block_height()
    block_size = get_bitcoin_block_size()
    
    print(f"Bitcoin Hashrate: {hashrate} TH/s")
    print(f"Bitcoin Mining Difficulty: {difficulty}")
    print(f"Bitcoin Active Addresses: {active_addresses}")
    print(f"Bitcoin Block Height: {block_height}")
    print(f"Bitcoin Block Size: {block_size}")

if __name__ == "__main__":
    main()
