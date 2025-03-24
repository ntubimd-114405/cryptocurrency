from django.shortcuts import render
from data_analysis.train import kaggle

def home(request):
    # 取得最新 3 則新聞
    link = kaggle.create_kaggle_metadata(1, "testname")
    
    # 將 'a' 放入 context 字典中，傳遞到模板
    context = {
        'link': link
    }

    return render(request, 'ml_home.html', context)
