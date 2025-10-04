from django.shortcuts import render, get_object_or_404, redirect
from .models import Article, Website,Reply,Comment,XPost
from datetime import datetime
import re


def home(request):
    # 取得最新 3 則新聞
    latest_articles = Article.objects.all().order_by('-time')[:3]

    context = {
        'all_articles': latest_articles  # 傳遞新聞資料
    }
    return render(request, 'news_home.html', context)


# 2. 新聞詳細內容與留言、回覆機制-----------
def news_detail(request, article_id):
    article = get_object_or_404(Article, pk=article_id)
    content = article.content
    
    if request.method == 'POST':
        content = request.POST.get('content')
        parent_id = request.POST.get('parent_id')  # 確認是否是回覆評論
        
        if parent_id:  # 如果是回覆
            comment = get_object_or_404(Comment, pk=parent_id)
            Reply.objects.create(
                comment=comment,  # 回覆評論
                user=request.user,
                content=content
            )
        else:  # 如果是新增評論
            Comment.objects.create(
                article=article,
                user=request.user,
                content=content
            )
        
        return redirect('news_detail', article_id=article.id)

    comments = article.comments.all()
    return render(request, 'news_detail.html', {'article': article, 'comments': comments, 'content': content})
# 2. 新聞詳細內容與留言、回覆機制-----------

# 1. 新聞首頁與最新新聞展示-----------
def news_home(request):
    all_articles = Article.objects.all().order_by('-time')[:3]  # 查詢新聞文章

    return render(request, 'news_home.html', {
        'all_articles': all_articles,  # 傳遞新聞文章
    })
# -----------1. 新聞首頁與最新新聞展示


# 新聞列表翻頁-----------------
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from .models import Article, Website, Reply, Comment, XPost
from datetime import datetime
import re

from django.db.models import Q
from datetime import datetime
from django.core.paginator import Paginator
from django.shortcuts import render
from .models import Article


# 3. 新聞搜尋、關鍵字與日期篩選 + 分頁-----------
def news_list(request):
    query = request.GET.get('q', '')  # 搜尋關鍵字
    start_date = request.GET.get('start_date', '')  # 開始日期
    end_date = request.GET.get('end_date', '')  # 結束日期
    page = request.GET.get('page', 1)  # 當前頁碼

    # 篩選 title、content、time 不為空的資料
    all_articles = Article.objects.filter(
        ~Q(title__isnull=True),
        ~Q(title=''),
        ~Q(content__isnull=True),
        ~Q(content=''),
        ~Q(time__isnull=True)
    )

    # 若有關鍵字，再進行額外搜尋條件
    if query:
        all_articles = all_articles.filter(title__icontains=query)

    # 日期範圍篩選
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        all_articles = all_articles.filter(time__gte=start_date)
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        all_articles = all_articles.filter(time__lte=end_date)

    # 根據時間倒序排序
    all_articles = all_articles.order_by('-time')

    # 分頁
    paginator = Paginator(all_articles, 5)
    paged_articles = paginator.get_page(page)

    return render(request, 'news_list.html', {
        'all_articles': paged_articles,
        'query': query,
        'start_date': start_date,
        'end_date': end_date,
    })
# -----------3. 新聞搜尋、關鍵字與日期篩選 + 分頁


# 計算情緒百分比並顯示在文章詳細頁面
from django.shortcuts import render, get_object_or_404
from .models import Article, Comment  # 假設你的模型名稱為 Article 和 Comment


# 4. 新聞情緒分數圖表-----------
def article_detail(request, article_id):
    # 獲取文章和相關評論
    article = get_object_or_404(Article, id=article_id)
    comments = article.comments.all()

    # 正規化 sentiment_score (-1, 0, 1) 到 0-100 範圍
    sentiment_score = article.sentiment_score
    if sentiment_score == 1:
        normalized_score = 100  # 正面
        color = '#28a745'  # 綠色
    elif sentiment_score == 0:
        normalized_score = 50  # 中性
        color = '#ffc107'  # 黃色
    else:  # sentiment_score == -1
        normalized_score = 0  # 負面
        color = '#dc3545'  # 紅色

    # 圖表數據
    chart_data = {
        'normalized_score': normalized_score,
        'background_color': color,
        'sentiment_score': sentiment_score  # 保留原始分數以顯示
    }

    # 上下文數據
    context = {
        'article': article,
        'comments': comments,
        'chart_data': chart_data
    }
    return render(request, 'article_detail.html', context)
# -----------4. 新聞情緒分數圖表


from django.shortcuts import render
from django.http import JsonResponse
from django.urls import reverse
from datetime import datetime, date
from data_analysis.crypto_ai_agent.news_agent import search_news  # 你的搜尋函數

# 5.進階搜尋 API 與資料整合（後端/前端）-----------
def search_news_api(request):
    """
    搜尋新聞 API
    GET 參數：
        - question: 搜尋關鍵字
        - start_date: yyyy-mm-dd
        - end_date: yyyy-mm-dd
    """
    question = request.GET.get("question", "BTC")
    start_date_str = request.GET.get("start_date", "2025-01-01")
    end_date_str = request.GET.get("end_date", "2025-10-02")


    try:
        results = search_news(
            question,
            start_date=start_date_str,
            end_date=end_date_str,
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    # 從 search_news 結果取出所有 id
    ids = [r.get("id") for r in results if r.get("id")]

    # 一次查詢所有文章
    articles = Article.objects.filter(id__in=ids).select_related("website")

    # 建立 dict，方便用 id 找文章
    article_map = {a.id: a for a in articles}

    news_data = []
    for r in results:
        article_id = r.get("id")
        try:
            article_id = int(article_id)  # 🔑 確保型別正確
        except (TypeError, ValueError):
            article_id = None
        db_article = article_map.get(article_id)
        if db_article:
            news_data.append({
                "id": db_article.id,
                "title": db_article.title,
                "summary": db_article.summary,
                "content": db_article.content,
                "url": db_article.url,
                "image_url": db_article.image_url,
                "time": db_article.time.strftime("%Y-%m-%d %H:%M") if db_article.time else "",
                "website": {
                    "name": db_article.website.name,
                    "url": db_article.website.url,
                    "icon_url": db_article.website.icon_url,
                },
                "sentiment_score": db_article.sentiment_score,
            })
        else:
            # 沒找到的話就保留基本資料
            news_data.append({
                "id": article_id,
                "title": r.get("title", "未知標題"),
                "summary": r.get("summary", ""),
            })

    return JsonResponse({"results": news_data})

# -------- HTML View --------
def search_news_page(request):
    """
    搜尋網頁頁面，透過 AJAX 呼叫 API
    """
    return render(request, "search_news_page.html")
# -----------5.進階搜尋 API 與資料整合（後端/前端）




def X_list(request):
    # 获取指定 id 的 XPost 对象
    xposts = XPost.objects.all()
    return render(request, 'x_list.html', {'xposts': xposts})