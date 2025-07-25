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


def news_home(request):
    all_articles = Article.objects.all().order_by('-time')[:3]  # 查詢新聞文章
    xposts = XPost.objects.all().order_by('-ids')[:3]  # 使用共用的函數來獲取 Twitter 貼文
    print(xposts)

    return render(request, 'news_home.html', {
        'all_articles': all_articles,  # 傳遞新聞文章
        'xposts': xposts,              # 傳遞 Twitter 貼文
    })

def X_list(request):
    # 获取指定 id 的 XPost 对象
    xposts = XPost.objects.all()
    return render(request, 'x_list.html', {'xposts': xposts})

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

# 新聞列表翻頁-----------------

from data_analysis.sentiment.api import predict_sentiment_api


def analyze_sentiment_by_id(request, article_id):
    article = get_object_or_404(Article, pk=article_id)

    if article.content:
        sentiment_result = predict_sentiment_api(article.content)
        article.sentiment = sentiment_result
        article.save(update_fields=['sentiment'])
        message = f"文章 (ID: {article_id}) 的情緒分析已完成，結果: {sentiment_result}"
    else:
        message = f"文章 (ID: {article_id}) 沒有內容，無法分析情緒"

    sentiment_label_map = {
        '-1': '負面',
        '0': '中立',
        '1': '正面',
        '-9': '信心不足',
        None: '尚未進行分析'
    }
    sentiment_label = sentiment_label_map.get(article.sentiment, '未知')

    return render(request, 'analyze_single_result.html', {
        'article': article,
        'message': message,
        'sentiment_label': sentiment_label,
    })