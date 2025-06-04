# <img src="static/images/crypto.png" alt="AI幣市通 Logo" width="80"/> AI幣市通


AI幣市通是一套結合人工智慧與資料視覺化技術的加密貨幣分析平台，專為幣圈投資人打造。平台提供即時幣價查詢、AI 預測模型、市場情緒分析與新聞聚合，協助使用者掌握趨勢、預測走勢、做出更明智的投資判斷。

---

## 📊 系統功能比較

| 功能 / 特色                  | **AI幣市通**             | CoinGecko             | TradingView           | Messari                   |
|-----------------------------|--------------------------|------------------------|------------------------|---------------------------|
| 1. 即時幣價顯示              | ✔ 有                     | ✔ 有                   | ❌ 以圖表為主          | ❌ 以研究為主             |
| 2. 幣價趨勢預測（AI 模型）  | ✔ 自家 AI 預測模型       | ❌ 無                  | ❌ 無                  | ❌ 無                      |
| 3. 資訊整合（新聞 + 數據）  | ✔ 自動爬蟲與彙整         | ✔ 有新聞整合          | ❌ 圖表為主            | ✔ 有產業分析報告         |
| 4. 技術分析圖表              | ✔ 互動式技術分析圖表     | ✔ 基本圖表            | ✔ 高階圖表            | ❌ 無                      |
| 5. AI 智能客服               | ✔ 有                     | ❌ 無                  | ❌ 無                  | ✔ 有（部分支援）         |
| 6. AI Agent 任務助手         | ✔ 任務導向式 AI Agent     | ❌ 無                  | ❌ 無                  | ✔ Messari AI Assistant    |
| 7. AI 個人化報告生成         | ✔ 自動化報告生成與摘要   | ❌ 無                  | ❌ 無                  | ✔ AI 報告摘要             |
---

## 🛠 使用技術 Technology Stack

| 類別 | 技術 |
|------|------|
| 後端框架 | Django (Python) |
| 資料庫 | MariaDB |
| 任務佇列 / 訊息代理 | RabbitMQ + Celery                                                   |
| 情緒分析模型 | ElKulako/cryptobert,mrm8488/distilroberta,AfterRain007/cryptobertRefined,ProsusAI/finbert |
| AI客服模型 | AdaptLLM/finance-chat |
| 前端 | HTML / CSS / JavaScript |

---

## 🗂 資料來源與更新頻率

| 類別             | 更新頻率 | 資料種類                              | 資料來源                                |
|------------------|----------|---------------------------------------|-----------------------------------------|
| 加密貨幣資訊     | 每日 1 次 | 名稱、圖示、市值等                   | [CoinMarketCap API](https://coinmarketcap.com/api/) |
| 加密貨幣價格     | 每 10 分鐘 | 最高價、最低價、交易量等             | [CCXT](https://github.com/ccxt/ccxt)    |
| 新聞爬蟲         | 每小時    | 標題、內文、新聞圖片等               | [CoinDesk](https://www.coindesk.com/)、[Yahoo Finance](https://finance.yahoo.com) |
| 宏觀經濟數據     | 每日 1 次 | GDP、失業率、CPI 等                  | [FRED API](https://fred.stlouisfed.org/) |
| 其他金融與鏈上資料 | 每小時    | S&P500、美元指數、哈希率、挖礦難度等 | [yfinance](https://pypi.org/project/yfinance/)、[Blockchain.com API](https://www.blockchain.com/api) |


---


## 📬 聯絡資訊

開發者：陳建璋、陳紹維、何竑蓄、江以丞

學校/系所：台北商業大學資訊管理系

指導老師：劉志華

Email：1114608@ntub.edu.tw

