from django.shortcuts import render, get_object_or_404, redirect
from .models import Article, Website,Reply,Comment
from datetime import datetime
import re


def home(request):

    context = {

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