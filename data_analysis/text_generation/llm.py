import os
import warnings

# 隱藏所有警告訊息
warnings.filterwarnings('ignore')

# 設定 TensorFlow oneDNN 警告
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch

# 設置裝置
device = "cuda" if torch.cuda.is_available() else "cpu"

# 模型名稱
model_name = "AdaptLLM/finance-LLM"

# 建立量化設定
bnb_config = BitsAndBytesConfig(
    load_in_8bit=True,               # 啟用 8bit 模式
    llm_int8_threshold=6.0,          # 可選：控制轉換精度閾值
    llm_int8_has_fp16_weight=False,  # 若顯卡較老建議設為 False
    device_map="auto"                # 自動將模型對映到可用 GPU
)

# 函數：根據提示生成文本
def generate_text_from_prompt(prompt: str) -> str:
    """
    根據給定的提示生成文本。
    
    :param prompt: 提示文本
    :return: 生成的文本
    """
    # 載入 tokenizer 和量化模型
    tokenizer = AutoTokenizer.from_pretrained(model_name, legacy=False)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config
    )

    # 編碼輸入
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    # 生成結果
    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_length=200,
            temperature=0.7,
            do_sample=True  # 啟用隨機抽樣
        )
        '''
        outputs = self.model.generate(
            inputs["input_ids"],
            max_length=max_length,
            do_sample=True,
            temperature=0.7,
            top_k=50,
            top_p=0.95,
            repetition_penalty=1.1,
            eos_token_id=self.tokenizer.eos_token_id
        )
        '''

    # 解碼輸出
    result = tokenizer.decode(output[0], skip_special_tokens=True)

    return result



# 測試範例
if __name__ == "__main__":
    prompt = "Analyze the impact of interest rate hikes on the stock market:"
    generated_output = generate_text_from_prompt(prompt)
    print("Generated Output:")
    print(generated_output)
