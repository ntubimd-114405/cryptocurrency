# 常用指令
celery -A cryptocurrency worker --loglevel=info
celery -A cryptocurrency worker --loglevel=info -P eventlet
celery -A cryptocurrency worker --loglevel=info -P gevent
celery -A cryptocurrency worker --loglevel=info --pool=solo

celery -A cryptocurrency beat --loglevel=info

set DJANGO_SETTINGS_MODULE=cryptocurrency.settings

git merge team/main

# Cuda
https://developer.nvidia.com/cuda-11-8-0-download-archive
https://developer.nvidia.com/rdp/cudnn-archive
# 創建虛擬環境
python -m venv env

# 啟動虛擬環境（Windows）
env\Scripts\activate

# Cryptocurrency
這裡放上你專案的簡短描述或介紹。

# 安裝
pip install -r requirements.txt

# 使用方法
提供使用你項目的指示。你可以包含代碼範例或截圖。

# 貢獻
解釋其他人如何貢獻到你的項目，例如報告錯誤、提出改進建議或提交拉取請求。

# 授權
指定你的專案分發的授權條款。

# 鳴謝
感謝所有貢獻或啟發你的人。

# 聯絡
提供聯絡方式（例如電子郵件或社交媒體），讓使用者可以向你提問或提供回饋。
