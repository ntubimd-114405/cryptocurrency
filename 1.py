import pandas as pd
import MySQLdb
from dotenv import load_dotenv
import os
from pathlib import Path
from datetime import datetime

env_path = Path(__file__).resolve().parents[0] / '.env'

# 加載 .env 檔案
load_dotenv(dotenv_path=env_path)

conn = MySQLdb.connect(
    host="localhost",
    user=os.getenv('DB_USER'),
    passwd=os.getenv('DB_PASSWORD'),
    db="cryptocurrency",
    charset="utf8mb4"
)

query = "SELECT * FROM main_coinhistory"
df = pd.read_sql(query, conn)

# 匯出 CSV
df.to_csv("coin.csv", index=False)
conn.close()