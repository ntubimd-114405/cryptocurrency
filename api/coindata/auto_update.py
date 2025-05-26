import schedule
import time
from all import main  # 替換為你的 main 函式來源

def job():
    print("⏰ 每 30 分鐘執行一次")
    main(1)

# 每 30 分鐘執行一次
schedule.every(30).minutes.do(job)

# 持續執行
while True:
    schedule.run_pending()
    time.sleep(1)
