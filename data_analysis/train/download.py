import kaggle
import os

def check_notebook_status(folder_id,name):
    kaggle_username = os.getenv("KAGGLE_USERNAME")
    notebook_id = f"{kaggle_username}/crypto-{folder_id}-{name}"
    result=kaggle.api.kernels_status(notebook_id)
    result_dict = result.to_dict()

    # 提取狀態
    status = result_dict.get("status", "unknown")  # 預設值為 "unknown"
    failure = result_dict.get("failureMessage", "unknown")

    print(f"Notebook 狀態: {status},錯誤訊息{failure}:")
    return status #RUNNING  COMPLETE
    
def download_output(folder_id,name):
    kaggle_username = os.getenv("KAGGLE_USERNAME")
    folder_path = f"media/kaggle/{folder_id}/output"
    notebook_id = f"{kaggle_username}/crypto-{folder_id}-{name}"
    try:
        kaggle.api.kernels_output(notebook_id,folder_path)
    except Exception as e:
        print(f"發生錯誤: {e}")
    return f"成功下載{notebook_id}至{folder_path}"

if __name__ == "__main__":
    print(check_notebook_status(11,"testname"))
    print(download_output(11,"testname"))


