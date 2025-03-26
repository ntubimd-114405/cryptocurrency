import os
import json
import shutil
import subprocess
import sys

def create_kaggle_metadata(folder_id,name):
    folder_path = f"media/kaggle/{folder_id}"
    os.makedirs(folder_path, exist_ok=True)
    
    metadata_file = os.path.join(folder_path, "kernel-metadata.json")
    new_notebook_path = os.path.join(folder_path, "1.ipynb")

    kaggle_username = os.getenv("KAGGLE_USERNAME")
    # 測試用
    metadata = {
        "id": f"{kaggle_username}/crypto-{folder_id}-{name}",
        "title": f"crypto-{folder_id}-{name}",
        "code_file": "1.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": "false",
        "enable_gpu": "true",
        "enable_tpu": "false",
        "enable_internet": "true",
        "dataset_sources": ["fgh09101010/merge-data-1h-and-1d"],
        "competition_sources": [],
        "kernel_sources": [],
        "model_sources": [],
        "kernelspec": {
            "display_name": "Python 3",
            "name": "python3"
        }
    }

    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    modify_and_save_notebook(new_notebook_path)
    push_kaggle_kernel(folder_id)

    return f"https://www.kaggle.com/code/fgh09101010/crypto-{folder_id}-{name}"

def modify_and_save_notebook(new_path):
    template_path = "data_analysis/train/template/test.ipynb"
    # 先複製原始 notebook，確保原始檔案不受影響
    shutil.copy(template_path, new_path)

    # 讀取新的 notebook 檔案
    with open(new_path, "r", encoding="utf-8") as f:
        notebook = json.load(f)
    
    # 修改 notebook 內容
    for cell in notebook.get("cells", []):
        if cell.get("cell_type") == "code":
            cell["source"] = [feature_create()]
            break

    # 存回修改後的 notebook
    with open(new_path, "w", encoding="utf-8") as f:
        json.dump(notebook, f, indent=2, ensure_ascii=False)

    print(f"已成功修改並儲存為 {new_path}")


def push_kaggle_kernel(folder_id):


    folder_path = f"media/kaggle/{folder_id}"
    
    # 檢查資料夾是否存在
    if not os.path.exists(folder_path):
        print(f"錯誤: {folder_path} 不存在，請先創建資料夾。")
        return
    # 獲取虛擬環境中的 Scripts 資料夾路徑
    kaggle_username = os.getenv("KAGGLE_USERNAME")
    kaggle_key = os.getenv("KAGGLE_KEY")
    os.environ["KAGGLE_USERNAME"] = kaggle_username
    os.environ["KAGGLE_KEY"] = kaggle_key

    venv_scripts_path = os.path.join(os.path.dirname(sys.executable))
    # 構造 kaggle.exe 的完整路徑
    kaggle_exe_path = os.path.join(venv_scripts_path, 'kaggle.exe')

    # 構造要執行的命令
    command = f'"{kaggle_exe_path}" kernels push -p "{folder_path}"'
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    # 輸出執行結果
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print("錯誤:", result.stderr)

    print(f"已執行: {command}")

def feature_create():
    feature_list = [
            'close_price', 
            'S&P 500 Index', 
            'VIX Volatility Index', 
            'WTI Crude Oil Futures', 
            'US Dollar Index', 
            'Gold Futures', 
            'volume', 
            "positive", 
            "neutral", 
            "negative", 
            "Average Block Size",
            "Difficulty", 
            "Hash Rate", 
            "Miners Revenue", 
            "Number Of Unique Addresses Used",
            'open_price', 
            'high_price', 
            'low_price']
    feature_str = "features = [\n"
    for feature in feature_list:
        feature_str += f"            '{feature}', \n"
    feature_str = feature_str.rstrip(", \n")  # 移除最後的逗號和換行
    feature_str += "\n]"
    return feature_str


if __name__ == "__main__":
    print(create_kaggle_metadata(9,"abcdefg"))


