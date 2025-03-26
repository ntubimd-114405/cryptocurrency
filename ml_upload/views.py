from django.shortcuts import render
from data_analysis.train import upload
from data_analysis.train import download
import os
import pandas as pd
import plotly.graph_objects as go
from django.conf import settings


def home(request):
    # 取得最新 3 則新聞
    link = upload.create_kaggle_metadata(1, "testname")
    
    # 將 'a' 放入 context 字典中，傳遞到模板
    context = {
        'link': link
    }

    return render(request, 'ml_home.html', context)

def notebook_status(request):
    """Notebook 狀態頁面：顯示狀態，若完成則下載輸出"""
    status = download.check_notebook_status(1, "testname")

    output_result = download.download_output(1, "testname")

    folder_path = f"media/kaggle/1/output"

    context = {
        'status': status,
        'output_result': output_result,
        'chart_html':plot_prediction_chart()
    }
    return render(request, 'notebook_status.html', context)

def plot_prediction_chart():
    # 設定 CSV 路徑
    csv_path = os.path.join(settings.BASE_DIR, "media/kaggle/1/output/pred.csv")

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