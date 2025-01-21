import websocket
import json
import MySQLdb
import os
from datetime import datetime

def save_data(data):
    # 連接到 MySQL 資料庫
    conn = MySQLdb.connect(
        host="localhost",
        user=os.getenv('DB_USER'),
        passwd=os.getenv('DB_PASSWORD'),
        db="cryptocurrency",
        charset="utf8mb4"
    )

    # 創建 cursor 物件
    cursor = conn.cursor()

    # 檢查是否已經存在相同的 `last_update_id`
    check_query = """
    SELECT COUNT(*) FROM main_depthdata
    WHERE last_update_id = %s;
    """
    cursor.execute(check_query, (data["lastUpdateId"],))
    result = cursor.fetchone()

    if result[0] > 0:
        # 如果已經存在相同的資料，則跳過插入
        print(f"資料已存在：{data['lastUpdateId']}，跳過插入。")
    else:
        # 如果不存在，則執行插入操作
        query = """
        INSERT INTO main_depthdata (last_update_id, bids, asks, created_at, coin_id)
        VALUES (%s, %s, %s, %s, %s);
        """
        # 假設您會將 `coin_id` 參數傳入
        # 在這裡，我假設 `coin_id` 是預設的 ID (例如 1)，您可以根據需要來替換
        coin_id = 1  # 這個應該是根據您的需求來決定

        # 執行插入操作
        cursor.execute(query, (
            data["lastUpdateId"],
            json.dumps(data["bids"]),
            json.dumps(data["asks"]),
            datetime.now(),
            coin_id
        ))

        # 提交事務
        conn.commit()

        # 顯示插入的資料
        print(f"資料已插入：{data['lastUpdateId']}, {data['bids']}, {data['asks']}")

    # 關閉連接
    cursor.close()
    conn.close()

def on_message(ws, message):
    # 解析接收到的消息
    data = json.loads(message)
    print("接收到的資料:", message)
    
    # 保存資料到資料庫
    save_data(data)

# Binance WebSocket URL
url = "wss://stream.binance.com:9443/ws/btcusdt@depth5"

# 建立 WebSocket 連接
ws = websocket.WebSocketApp(url, on_message=on_message)

# 開始接收 WebSocket 訊息並持續運行
ws.run_forever()
