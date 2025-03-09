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


def news_list(request):
    # 獲取搜尋關鍵字和篩選選項
    query = request.GET.get('q', '')  # 搜尋關鍵字
    start_date = request.GET.get('start_date', '')  # 開始日期
    end_date = request.GET.get('end_date', '')  # 結束日期
    
    # 基本篩選邏輯
    if query:
        all_articles = Article.objects.filter(title__icontains=query)
    else:
        all_articles = Article.objects.all()
    
    # 如果提供了日期範圍，則進行日期篩選
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')  # 解析日期格式
        all_articles = all_articles.filter(time__gte=start_date)
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        all_articles = all_articles.filter(time__lte=end_date)
    
    # 根據時間倒序排序
    all_articles = all_articles.order_by('-time')[:10]

    return render(request, 'news_list.html', {'all_articles': all_articles, 'query': query})


def news_detail(request, article_id):
    article = get_object_or_404(Article, pk=article_id)
    content = article.content
    paragraphs = re.split(r'([。!?])', content)
    paragraphs = [f'{paragraphs[i]}{paragraphs[i+1]}' for i in range(0, len(paragraphs)-1, 2)]
    
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
    return render(request, 'news_detail.html', {'article': article, 'comments': comments, 'paragraphs': paragraphs})

from django.shortcuts import render
from .models import Article, XPost  # 確保你有這些模型

# 共用的 X_list 邏輯
def get_xposts():
    return XPost.objects.all()

def news_home(request):
    all_articles = Article.objects.all().order_by('-time')[:3]  # 查詢新聞文章
    xposts = XPost.objects.all().order_by('-ids')[:3]  # 使用共用的函數來獲取 Twitter 貼文
    print(xposts)

    return render(request, 'news_home.html', {
        'all_articles': all_articles,  # 傳遞新聞文章
        'xposts': xposts,              # 傳遞 Twitter 貼文
    })

def X_list(request):
    # 获取所有 XPost 对象，使用相同的函數來避免重複
    xposts = get_xposts()
    return render(request, 'x_list.html', {'xposts': xposts})


def X_list(request):
    # 获取指定 id 的 XPost 对象
    xposts = XPost.objects.all()
    return render(request, 'x_list.html', {'xposts': xposts})