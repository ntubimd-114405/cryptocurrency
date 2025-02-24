import requests
from datetime import datetime, timezone

def convert_data(data):
    if 'values' not in data or not isinstance(data['values'], list):
        # 返回一個適當的錯誤消息或空數據結構
        return {
            "name": data.get("name", "Hash Rate"),
            "unit": data.get("unit", ""),
            "period": data.get("period", ""),
            "description": data.get("description", ""),
            "values": [],  # 返回空的值
            "error": "No valid values found"  # 可選的錯誤訊息
        }
    
    values_array = [
        [datetime.fromtimestamp(entry['x'], tz=timezone.utc).isoformat(), entry['y']]
        for entry in data['values']
    ]
    result = {
        "name": data.get("name", "Hash Rate"),
        "unit": data.get("unit", ""),
        "period": data.get("period", ""),
        "description": data.get("description", ""),
        "values": values_array
    }
    return result

def get_bitcoin_data(chart_name, start_time):
    url = f"https://api.blockchain.info/charts/{chart_name}?timespan=1year&format=json&start={start_time}"
    response = requests.get(url)
    data = response.json()
    return convert_data(data)

def get_all_data(name, start_time):
    chart_mapping = {
        "Hash Rate": "hash-rate",
        "Number Of Unique Addresses Used": "n-unique-addresses",
        "Average Block Size": "avg-block-size",
        "Miners Revenue":"miners-revenue",
        "Mempool Size":"mempool-size",
        "Difficulty":"difficulty",
    }
#,"miners-revenue","mempool-size","difficulty"]
    chart_name = chart_mapping.get(name)
    if chart_name:
        return get_bitcoin_data(chart_name, start_time)
    return None