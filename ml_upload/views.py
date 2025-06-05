from django.shortcuts import render, redirect, get_object_or_404
from data_analysis.train import upload
from data_analysis.train import download
from data_analysis.train2 import api
import os
import pandas as pd
import plotly.graph_objects as go
from django.conf import settings
from .models import *
from .forms import DataLocationForm
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    # 查詢所有 DataLocation 物件
    data_locations = DataLocation.objects.all()

    # 傳遞到模板
    return render(request, 'ml_home.html', {'data_locations': data_locations})

@login_required
def add_data_location(request):
    if request.method == 'POST':
        # 如果是 POST 請求，則表單提交
        form = DataLocationForm(request.POST)
        if form.is_valid():
            # 在保存前手動填充 user 欄位
            new_data_location = form.save(commit=False)
            new_data_location.user = request.user  # 設置當前用戶為該資料的擁有者
            new_data_location.save()  # 保存資料到資料庫
            return redirect('ml_home')  # 重新導向到資料列表頁面
    else:
        # 如果是 GET 請求，則顯示空白表單
        form = DataLocationForm()

    return render(request, 'add_data_location.html', {'form': form})

@login_required
def data_location_detail(request, id):
    # 使用 get_object_or_404 確保當資料不存在時返回 404 錯誤
    data_location = get_object_or_404(DataLocation, id=id)
    
    status = None
    output_result = None

    folder_path = f"media\model\{id}"
    chart_html = plot_prediction_chart(folder_path)

    context = {
        'data_location': data_location,
        'status': status,
        'output_result': output_result,
        'chart_html': chart_html
    }
    # 渲染 template，並傳遞 data_location 實例
    return render(request, 'data_location_detail.html',context)


def plot_prediction_chart(folder_path):
    # 設定 CSV 路徑
    csv_path = os.path.join(settings.BASE_DIR, f"{folder_path}\pred.csv")

    if not os.path.exists(csv_path):
        return None

    # 讀取 CSV
    df = pd.read_csv(csv_path)
    df["Date"] = pd.to_datetime(df["Date"])  # 確保 Date 欄位為 datetime 格式

    # 建立 Plotly 圖表
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Date"], y=df["Actual Price"], mode="lines+markers", name="Actual Price"))
    fig.add_trace(go.Scatter(x=df["Date"], y=df["Predicted Price"], mode="lines+markers", name="Predicted Price", line=dict(dash="dash")))

    # 設定標題與座標軸
    fig.update_layout(
        title="Actual vs Predicted Price",
        xaxis_title="Date",
        yaxis_title="Price",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True),
        template="plotly_dark",  # 可改成 "plotly" (白底) 或 "plotly_dark" (黑底)
    )

    # 轉換圖表為 HTML
    chart_html = fig.to_html(full_html=False)

    return chart_html

@login_required
def run_program(request, id):
    # 獲取對應的 DataLocation 實例
    data_location = get_object_or_404(DataLocation, id=id)
    
    features = [
            'close_price', 
            'S&P 500 Index', 
            'VIX Volatility Index', 
            'WTI Crude Oil Futures', 
            'US Dollar Index', 
            'Gold Futures', 
            'volume', 
            'positive', 
            'neutral', 
            'negative', 
            'Average Block Size', 
            'Difficulty', 
            'Hash Rate', 
            'Miners Revenue', 
            'Number Of Unique Addresses Used', 
            'open_price', 
            'high_price', 
            'low_price'
    ]
    features = [f.strip() for f in data_location.features.split(',') if f.strip()]
    api.prediction_api(str(id),features)
    data_location.status = "Running"
    data_location.save()  # 保存更改
    return redirect('data_location_detail', id=id)