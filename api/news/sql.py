import mysql.connector
from dotenv import load_dotenv
import os
from pathlib import Path

# 設定 .env 檔案的路徑
env_path = Path(__file__).resolve().parents[3] / '.env'

# 加載 .env 檔案
load_dotenv(dotenv_path=env_path)

def insert_sql(website_name, articles):
    try:
        # 資料庫連接配置
        conn = mysql.connector.connect(
            host="localhost",  # 替換為你的資料庫主機地址
            user=os.getenv('DB_USER'),  # 替換為你的用戶名
            password=os.getenv('DB_PASSWORD'),  # 替換為你的密碼
            database="cryptocurrency",  # 替換為你的資料庫名稱
            time_zone="+08:00"  # 設定為台灣時間
        )

        cursor = conn.cursor()

        # 檢查網站是否存在
        select_website_query = "SELECT id FROM `main_newswebsite` WHERE `name` = %s"
        cursor.execute(select_website_query, (website_name,))
        website_id = cursor.fetchone()

        # 如果找不到對應的網站資料，則插入新網站
        if website_id is None:
            insert_website_query = "INSERT INTO `main_newswebsite` (`name`) VALUES (%s)"
            cursor.execute(insert_website_query, (website_name,))
            conn.commit()  # 確保資料插入後獲取新 ID
            website_id = cursor.lastrowid  # 獲取新增記錄的 ID
        else:
            website_id = website_id[0]  # 提取 website_id

        # 插入文章資料
        insert_article_query = """
        INSERT INTO `main_newsarticle` (`title`, `url`, `time`, `website_id`,`image_url`)
        VALUES (%s, %s, %s, %s, %s)
        """
        
        # 檢查文章是否已存在
        check_article_query = "SELECT 1 FROM `main_newsarticle` WHERE `title` = %s"
        
        # 插入每篇文章資料
        for article in articles:
            cursor.execute(check_article_query, (article[0],))
            existing_article = cursor.fetchone()

            if existing_article is None:  # 如果該標題不存在
                cursor.execute(insert_article_query, (article[0], article[1], article[2], website_id,article[3]))

        # 提交變更
        conn.commit()

        # 關閉遊標和連接
        cursor.close()
        conn.close()

        print(f"{website_name}資料成功插入！")
    except:
        print(f"{website_name}出現錯誤")
        print(f"錯誤訊息: {Exception}")

def no_content():
    try:
        # 資料庫連接配置
        conn = mysql.connector.connect(
            host="localhost",  # 替換為你的資料庫主機地址
            user=os.getenv('DB_USER'),  # 替換為你的用戶名
            password=os.getenv('DB_PASSWORD'),  # 替換為你的密碼
            database="cryptocurrency",  # 替換為你的資料庫名稱
            time_zone="+08:00"  # 設定為台灣時間
        )

        cursor = conn.cursor()

        # 查詢 content 為 NULL 的文章
        select_query = """
        SELECT id, website_id, url
        FROM main_newsarticle
        WHERE content IS NULL
        """
        
        cursor.execute(select_query)
        articles = cursor.fetchall()

        # 顯示結果
        data=[]
        if articles:
            for article in articles:
                data.append([article[0],article[1],article[2]])
        else:
            print("No articles found with no content.")

        # 關閉遊標和連接
        cursor.close()
        conn.close()
        return data
    except:
        print(f"no_content()出現錯誤")
        print(f"錯誤訊息: {Exception}")
        return []

def insert_content(id, data):
    try:
        # 資料庫連接配置
        conn = mysql.connector.connect(
            host="localhost",  # 替換為你的資料庫主機地址
            user=os.getenv('DB_USER'),  # 替換為你的用戶名
            password=os.getenv('DB_PASSWORD'),  # 替換為你的密碼
            database="cryptocurrency",  # 替換為你的資料庫名稱
            time_zone="+08:00"  # 設定為台灣時間
        )

        cursor = conn.cursor()

        # 查詢 image_url 是否已經存在
        check_query = "SELECT image_url FROM main_newsarticle WHERE id = %s"
        cursor.execute(check_query, (id,))
        result = cursor.fetchone()

        if result[0]:
            # 只更新 content
            update_query = """
            UPDATE main_newsarticle
            SET content = %s
            WHERE id = %s
            """
            cursor.execute(update_query, (data[0], id))
        else:
            # 如果 image_url 不存在，則更新 content 和 image_url
            update_query = """
            UPDATE main_newsarticle
            SET content = %s, image_url = %s
            WHERE id = %s
            """
            cursor.execute(update_query, (data[0], data[1], id))
        
        # 提交更改並關閉遊標和連接
        conn.commit()
        cursor.close()
        conn.close()
    except:
            print(f"{id}出現錯誤")
            print(f"錯誤訊息: {Exception}")
    


def insert_image_url(name, icon_url):
    try:
        # 資料庫連接配置
        conn = mysql.connector.connect(
            host="localhost",  # 替換為你的資料庫主機地址
            user=os.getenv('DB_USER'),  # 替換為你的用戶名
            password=os.getenv('DB_PASSWORD'),  # 替換為你的密碼
            database="cryptocurrency",  # 替換為你的資料庫名稱
            time_zone="+08:00"  # 設定為台灣時間
        )

        cursor = conn.cursor()

        # 插入資料
        insert_query = """
        INSERT INTO main_newswebsite (name, icon_url)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE icon_url = VALUES(icon_url)
        """

        # 執行插入或更新
        cursor.execute(insert_query, (name, icon_url))
        
        # 提交更改並關閉遊標和連接
        conn.commit()
        cursor.close()
        conn.close()
    except:
        print(f"{name}出現錯誤")
        print(f"錯誤訊息: {Exception}")