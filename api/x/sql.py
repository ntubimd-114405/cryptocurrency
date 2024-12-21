import mysql.connector
from dotenv import load_dotenv
import os
from pathlib import Path

# 設定 .env 檔案的路徑
env_path = Path(__file__).resolve().parents[3] / '.env'

# 加載 .env 檔案
load_dotenv(dotenv_path=env_path)

def insert_xpost(ids, html,text):
    conn = mysql.connector.connect(
        host="localhost",  # 替換為你的資料庫主機地址
        user=os.getenv('DB_USER'),  # 替換為你的用戶名
        password=os.getenv('DB_PASSWORD'),  # 替換為你的密碼
        database="cryptocurrency",  # 替換為你的資料庫名稱
        time_zone="+08:00"  # 設定為台灣時間
    )

    cursor = conn.cursor()

    # 插入操作
    insert_query = """
    INSERT IGNORE INTO main_xpost (ids, html,text)
    VALUES (%s, %s,%s)
    """

    cursor.execute(insert_query, (ids, html,text))
    conn.commit()

    # 关闭连接
    cursor.close()
    conn.close()
    print(f"{ids}資料成功插入！")
