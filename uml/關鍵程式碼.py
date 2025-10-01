'''
https://carbon.now.sh/
'''
# 表 9-1-2 關鍵程式(情緒分析)

def predict_sentiment(text):
    # 定義要使用的情緒分析模型以及它們的標籤對應分數
    # 格式為 (模型名稱, {模型輸出標籤: 對應分數})
    models_info = [
        ("ElKulako/cryptobert", {"Bearish": -1, "Neutral": 0, "Bullish": 1}),
        ("mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis", {"positive": 1, "negative": -1, "neutral": 0}),
        ("AfterRain007/cryptobertRefined", {"Bullish": 1, "Bearish": -1, "Neutral": 0}),
        ("ProsusAI/finbert", {"positive": 1, "negative": -1, "neutral": 0})
    ]

    # 用來儲存每個模型對該文本的情緒分數
    model_scores = []

    # 逐一使用每個模型進行情緒分析
    for model_name, sentiment_map in models_info:
        # 調用 analyze_sentiment_weighted 函式取得模型的加權情緒分數
        # text: 要分析的文本
        # model_name: 模型名稱
        # sentiment_map: 模型輸出標籤對應的分數映射
        # device: 運行設備，如 'cpu' 或 'cuda'
        score = analyze_sentiment_weighted(text, model_name, sentiment_map, device)
        
        # 將該模型分數加入列表
        model_scores.append(score)

    # 計算所有模型分數的平均值，作為最終的情緒分數
    # 如果沒有模型得分，則回傳 0.0
    final_score = sum(model_scores) / len(model_scores) if model_scores else 0.0

    # 回傳最終平均分數
    return final_score


# 表 9-1-3 關鍵程式(情緒分析加權)

def analyze_sentiment_weighted(text, model_name, sentiment_map, device, max_length=512):
    # 載入指定模型的 tokenizer，用於將文字轉換成模型可處理的格式
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    # 將長文本切分成多個小段，避免超過模型最大長度限制
    # max_tokens: 每段文字的最大 token 數量
    text_chunks = split_long_text(text, tokenizer, max_tokens=max_length)

    # 取得 HuggingFace 的情緒分析 pipeline
    # pipeline_model 可以直接對文字進行情緒分析，輸出 label 與 confidence score
    pipeline_model = get_sentiment_pipeline(model_name, device)

    # 初始化加權分數總和與計數器
    total_weighted_score = 0.0
    count = 0

    # 逐段文字計算情緒分數
    for chunk in text_chunks:
        # 對文字段落進行情緒分析
        result = pipeline_model(chunk, truncation=True, max_length=max_length)[0]
        label = result['label']  # 模型輸出的情緒標籤
        score = result['score']  # 模型對該標籤的信心分數（0~1）
        
        # 將模型標籤映射為數值情緒值，例如 -1, 0, 1
        sentiment_value = float(sentiment_map.get(label, 0))
        
        # 計算加權分數：情緒值 * 模型信心分數
        weighted_score = sentiment_value * score
        
        # 累加加權分數
        total_weighted_score += weighted_score
        count += 1

    # 計算該模型對整段文字的平均加權情緒分數
    avg_score = total_weighted_score / count if count else 0.0

    # 根據閾值判斷情緒傾向
    # >0.2 視為正向，<-0.2 視為負向，其餘視為中性
    if avg_score > 0.2:
        sentiment = 1
    elif avg_score < -0.2:
        sentiment = -1
    else:
        sentiment = 0

    # 列印模型分析結果（平均分數與最終判斷）
    print(f"→ {model_name} 平均情緒分數：{avg_score:.4f}，判斷結果：{sentiment}")
    
    # 回傳平均加權分數（非整數，用於集成多模型時計算平均值）
    return avg_score


# 表 9-1-4 關鍵程式(新聞文字摘要)

def summarize_long_text(text):
    # 將長文本切分成多段，避免模型一次輸入過長導致截斷或效能問題
    chunks = chunk_text(text)
    
    # 用來存放每段的摘要結果
    partial_summaries = []
    
    # 逐段進行摘要
    for i, chunk in enumerate(chunks):
            
        # 使用 summarizer 模型對每段文字生成摘要
        # max_length: 摘要最大長度
        # min_length: 摘要最小長度
        # do_sample=False: 禁止隨機抽樣，生成固定摘要
        summary = summarizer(chunk, max_length=100, min_length=30, do_sample=False)
        
        # 取得摘要文字並加入列表
        partial_summaries.append(summary[0]['summary_text'])


    # 對所有段落摘要再做一次整合摘要，得到整篇文章的精簡總結
    if partial_summaries:
        combined = " ".join(partial_summaries)
        
        # 二次摘要，設定略長的 max_length，以保留主要資訊
        final_summary = summarizer(combined, max_length=120, min_length=40, do_sample=False)
        
        # 回傳最終摘要文字
        return final_summary[0]['summary_text']
    else:
        # 若所有段落摘要失敗，回傳 None
        return None



#表 9-1-5 關鍵程式(定時任務)

CELERY_BEAT_SCHEDULE = {
    #新聞爬蟲
    'news_crawler-every-1-hour': { 
        'task': 'news.tasks.news_crawler',
        'schedule': 3600.0, #每1小時執行一次
    },

    #新聞情緒分析
    'news_sentiment-every-1-hour': {
    'task': 'news.tasks.news_sentiment',  
    'schedule': 3600.0, #1小時
    },

    #新聞摘要
    'news_summary-every-1-hour': {
    'task': 'news.tasks.news_summary',  
    'schedule': 3600.0, #1小時
    },

    #加密貨幣ohlcv資料
    'fetch_history-every-1-hour': { 
        'task': 'main.tasks.fetch_history',  
        'schedule': 3600.0, #1小時
    },

    #加密貨幣資料
    'fetch_data-every-1-day': { 
        'task': 'main.tasks.fetch_and_store_coin_data',  
        'schedule': 86400.0, #1天
    },

    #宏觀經濟資訊
    'macro_economy-every-1-day': { 
        'task': 'other.tasks.macro_economy',  
        'schedule': 86400.0, #1天
    },

    #加密貨幣指標
    'update_bitcoin_metrics-every-1-hour': { 
        'task': 'other.tasks.update_bitcoin_metrics',  
        'schedule': 3600.0, #1小時
    },

    #金融數據
    'update_bitcoin_financial-every-1-day': { 
        'task': 'other.tasks.save_financial',  
        'schedule': 86400.0, #1天
    },
}


#表 9-1-6 關鍵程式(建置加密貨幣新聞向量資料庫)

def build_crypto_news_vector_store(
    db_location: str = "./vector_db/news",   # 向量資料庫存放位置
    model_name: str = "mxbai-embed-large",   # 用於產生文章向量的模型
    max_docs: int = 100,                     # 每次只抓取最新的前 N 篇文章
) -> Chroma:
    # 初始化向量化工具
    embeddings = OllamaEmbeddings(model=model_name)

    # 建立或載入向量資料庫
    vector_store = Chroma(
        collection_name="crypto_news_articles",   # 資料庫名稱
        persist_directory=db_location,             # 資料庫存放路徑
        embedding_function=embeddings,            # 向量化函式
    )

    # 取得已存在的文章 ID，避免重複加入
    existing_ids = set(vector_store.get()["ids"])

    # 從 Django 資料庫取得最新文章，必須有 summary 與 content
    articles = Article.objects.filter(
        summary__isnull=False, content__isnull=False
    ).order_by("-time")[:max_docs]

    documents, ids = [], []
    for article in articles:
        aid = str(article.id)  # 使用 Django 原始 id
        if aid in existing_ids:
            continue  # 避免重複加入
        # 將 title + summary 作為向量內容
        documents.append(Document(
            page_content=f"{article.title}\n{article.summary}",
            metadata={
                "url": article.url,                     # 文章 URL
                "date": str(article.time.date()),       # 文章日期，ISO 格式
            },
            id=aid
        ))
        ids.append(aid)

    # 如果有新的文件，加入向量資料庫
    if documents:
        vector_store.add_documents(documents, ids=ids)

    return vector_store

#表 9-1-7 關鍵程式(向量資料庫進行新聞搜尋)

def search_crypto_news(
    question: str,                        # 查詢問題 / 關鍵字
    start_date: Optional[str] = None,     # 起始日期，ISO 格式，例如 "2025-09-01"
    end_date: Optional[str] = None,       # 結束日期
    db_path: str = "./vector_db/news",    # 向量資料庫路徑
    embed_model: str = "mxbai-embed-large", # 向量化模型名稱
    top_k: int = 5,                        # 取最相似的前 K 篇文章
):
    # 初始化向量化工具
    embeddings = OllamaEmbeddings(model=embed_model)
    vector_store = Chroma(
        collection_name="crypto_news_articles",
        persist_directory=db_path,
        embedding_function=embeddings,
    )

    # --- 建立時間過濾條件 ---
    where = None
    date_filters = []
    if start_date:
        start_timestamp = int(datetime.fromisoformat(start_date).timestamp())
        date_filters.append({"date": {"$gte": start_timestamp}})
    if end_date:
        end_timestamp = int(datetime.fromisoformat(end_date).timestamp())
        date_filters.append({"date": {"$lte": end_timestamp}})
    if date_filters:
        # 如果有多個日期條件，使用 AND 結合
        where = {"$and": date_filters} if len(date_filters) > 1 else date_filters[0]

    # --- 執行向量相似度搜尋 ---
    docs = vector_store.similarity_search(
        query=question,
        k=top_k,
        filter=where
    )

    # 整理搜尋結果，只取 title / summary / id / date
    results = []
    for doc in docs:
        parts = doc.page_content.split("\n", 1)
        title = parts[0] if len(parts) > 0 else ""
        summary = parts[1] if len(parts) > 1 else ""

        results.append({
            "id": doc.id,                        # Django 資料庫文章 id
            "title": title,
            "summary": summary,
            "date": doc.metadata.get("date"),    # 文章日期
        })

    return results
