from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM

# ✅ 使用中文摘要模型（如果內容是中文）
# summarizer = pipeline("summarization", model="uer/t5-base-chinese-cluecorpussummary")
# 若是英文內容，使用 BART 模型
MODEL_NAME = "facebook/bart-large-cnn"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
summarizer = pipeline("summarization", model=model, tokenizer=tokenizer, device=0)
# 5-2 文章摘要主函式
# 將長文分段
def chunk_text(text, chunk_size=800):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def summarize_long_text(text):
    chunks = chunk_text(text)
    partial_summaries = []

    print(f"✂️ 文章分為 {len(chunks)} 段進行摘要")
    
    for i, chunk in enumerate(chunks):
        try:
            print(f"📄 正在處理第 {i+1} 段...")
            summary = summarizer(chunk, max_length=100, min_length=30, do_sample=False)
            partial_summaries.append(summary[0]['summary_text'])
        except Exception as e:
            print(f"⚠️ 第 {i+1} 段摘要失敗：{e}")

    # 對所有段落摘要再做一次整合摘要
    if partial_summaries:
        combined = " ".join(partial_summaries)
        print(f"🧠 對 {len(partial_summaries)} 個段落摘要進行二次總結...")

        max_model_length = 1024
        
        inputs = tokenizer(
            combined,
            max_length=max_model_length, # 使用模型的最大長度
            truncation=True,             # 進行截斷
            return_tensors="pt"
        )
        
        final_summary = summarizer(
            tokenizer.decode(inputs['input_ids'][0], skip_special_tokens=True),
            max_length=120, 
            min_length=40, 
            do_sample=False
        )
        return final_summary[0]['summary_text']
    else:
        return None


if __name__ == "__main__":
    text = (
        "MicroStrategy's Michael Saylor believes the U.S. can unlock up to $100 trillion in economic value over the next decade through a structured approach to digital assets. "
        "Saylor outlined a taxonomy categorizing digital assets into four classes: cryptocurrencies like Bitcoin, enterprise blockchain tokens, security tokens, and central bank digital currencies (CBDCs). "
        "He argues that this classification would reduce regulatory uncertainty and integrate digital assets seamlessly into the economy. "
        "Saylor envisions a future where Bitcoin serves as a global reserve asset, enterprise tokens enhance business processes, security tokens revolutionize capital markets, and CBDCs improve monetary systems. "
        "He calls for clear regulations to foster innovation while protecting investors. "
        "Saylor's optimistic outlook suggests that embracing digital assets could drive significant economic growth and transformation in the coming decade. "
        "However, he acknowledges challenges such as regulatory hurdles and market volatility that need to be addressed for this vision to be realized. "
        "Overall, Saylor sees digital assets as a key component of the future financial landscape, with the potential to unlock trillions in value if managed properly. "
        "He urges policymakers to create a supportive framework that encourages adoption while mitigating risks."
        "Saylor's perspective highlights the transformative potential of digital assets across various sectors of the economy. "
        "By categorizing these assets, he aims to clarify their roles and benefits, making it easier for businesses and investors to understand and utilize them effectively. "
        "This structured approach could lead to increased adoption and integration of digital assets into everyday financial activities, driving innovation and efficiency. "
        "Saylor emphasizes the importance of collaboration between regulators, industry leaders, and technologists to create a balanced ecosystem that fosters growth while ensuring stability and security. "
        "He believes that with the right policies in place, digital assets can become mainstream financial instruments that contribute significantly to global economic development."
        "Saylor's vision extends beyond just financial markets; he sees digital assets playing a crucial role in reshaping various industries by enabling new business models and enhancing existing processes. "
        "For instance, enterprise blockchain tokens could streamline supply chains, improve transparency, and reduce costs for businesses. "
        "Security tokens have the potential to democratize access to investment opportunities by allowing fractional ownership of assets like real estate or art. "
        "CBDCs could enhance payment systems by providing faster, more secure transactions while reducing reliance on traditional banking infrastructure."
    )
    print(summarize_long_text(text))
