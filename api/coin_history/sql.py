import MySQLdb
from dotenv import load_dotenv
import os
from pathlib import Path
from datetime import datetime

env_path = Path(__file__).resolve().parents[2] / '.env'

# 加載 .env 檔案
load_dotenv(dotenv_path=env_path)


def get_name(n=None):
    # 初始化交易所
    conn = MySQLdb.connect(
        host="localhost",
        user=os.getenv('DB_USER'),
        passwd=os.getenv('DB_PASSWORD'),
        db="cryptocurrency",
        charset="utf8mb4"
    )

    # 創建 cursor 物件
    cursor = conn.cursor()

    if n is not None:
        query = f"SELECT id, abbreviation FROM main_coin LIMIT {int(n)};"
    else:
        query = "SELECT id, abbreviation FROM main_coin;"

    # 執行查詢
    cursor.execute(query)

    # 獲取結果
    abbreviations = cursor.fetchall()

    # 關閉連接
    cursor.close()
    conn.close()

    return abbreviations


def save_data(coin_id, data):
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

    # 將字符串日期轉換為 DATETIME 格式
    date = datetime.strptime(data[0], '%Y-%m-%d %H:%M:%S')

    # 檢查是否已存在相同的 date 和 coin_id
    check_query = """
    SELECT COUNT(*) FROM main_coinhistory
    WHERE date = %s AND coin_id = %s;
    """
    cursor.execute(check_query, (date, coin_id))
    result = cursor.fetchone()

    if result[0] > 0:
        # 如果已經存在相同的資料，則跳過插入
        print(f"資料已存在：{date}, {coin_id}，跳過插入。")
    else:
        # 如果不存在，則執行插入操作
        query = """
        INSERT INTO main_coinhistory (date, open_price, high_price, low_price, close_price, volume, coin_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        # 執行插入操作
        cursor.execute(query, (date, data[1], data[2], data[3], data[4], data[5], coin_id))

        # 提交事務
        conn.commit()

        # 顯示插入的資料
        print(f"資料已插入：{date}, {data[1]}, {data[2]}, {data[3]}, {data[4]}, {data[5]}, {coin_id}")

    # 關閉連接
    cursor.close()
    conn.close()
