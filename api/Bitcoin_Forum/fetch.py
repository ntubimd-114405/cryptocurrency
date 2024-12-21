import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
# 設定要爬取的URL
#url = 'https://bitcointalk.org/index.php?board=30.0'中文網站
url = 'https://bitcointalk.org/index.php?board=1.0'

# 發送GET請求
response = requests.get(url)
data=[]
# 檢查是否請求成功
if response.status_code == 200:
    # 解析HTML頁面
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 找到所有 class="bordercolor" 的 table
    tables = soup.find_all('table', class_='bordercolor')
    
    # 檢查是否有找到這些表格
    if tables:
        # 迭代所有的 table，跳過前兩個
        for index, table in enumerate(tables):
            if index < 2:
                continue  # 跳過前兩個表格
            
            # 找到該表格中的所有 tr 元素
            rows = table.find_all('tr')
            
            # 迭代並處理每一行 tr，跳過第一行
            for row_index, row in enumerate(rows):
                if row_index == 0:
                    continue  # 跳過第一行
                
                # 檢查該行中是否包含具有 lockicon 或 stickyicon 的 img
                img_lock = row.find('img', id=lambda x: x and x.startswith('lockicon'))
                img_sticky = row.find('img', id=lambda x: x and x.startswith('stickyicon'))
                
                # 如果找到該類型的 img 元素，跳過該行
                if img_lock or img_sticky:
                    continue
                
                # 提取每一行的文本
                cells = row.find_all(['td', 'th'])  # 提取所有的單元格
                row_data = [cell.get_text(strip=True) for cell in cells]
                link_tag = cells[2].find('a')
                if not link_tag:
                    continue
                title = link_tag.get_text(strip=True)
                link = link_tag['href']

                time_cell = cells[6].find('span', class_='smalltext')
                if time_cell:
                    time_text = time_cell.get_text(strip=True)
                    raw_time = time_text.split('by')[0].strip()
                    
                    try:
                        if "Today" in raw_time:
                            current_date = datetime.now().date()
                            time_part = raw_time.split("at")[-1].strip()
                            date_time_str = f"{current_date} {time_part}"
                            input_format = "%Y-%m-%d %I:%M:%S %p"
                        elif "Yesterday" in raw_time:
                            yesterday_date = datetime.now().date() - timedelta(days=1)
                            time_part = raw_time.split("at")[-1].strip()
                            date_time_str = f"{yesterday_date} {time_part}"
                            input_format = "%Y-%m-%d %I:%M:%S %p"
                        else:
                            date_time_str = raw_time
                            input_format = "%B %d, %Y, %I:%M:%S %p"

                        parsed_date = datetime.strptime(date_time_str, input_format)
                        formatted_date = parsed_date.strftime("%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        formatted_date = "Invalid date"
                else:
                    formatted_date = "No date"

                # 輸出結果
                #標題,連結,發布者,答覆,觀看次數,最後一個留言
                d=[row_data[2],link,row_data[3],row_data[4],row_data[5],formatted_date]
                # 輸出每一行的資料
                data.append(d)
    else:
        print('No tables with class "bordercolor" found.')
else:
    print(f"Failed to retrieve the page. Status code: {response.status_code}")

#標題,連結,發布者,答覆,觀看次數,最後一個留言
print(data)
