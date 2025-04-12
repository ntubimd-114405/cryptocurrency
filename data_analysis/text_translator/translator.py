from googletrans import Translator

# 建立翻譯器實例（共用）
translator = Translator()

def translate_to_english(text):
    """
    將中文翻譯成英文
    :param text: 中文字串
    :return: 英文翻譯結果
    """
    result = translator.translate(text, src='zh-tw', dest='en')
    return result.text

def translate_to_chinese(text):
    """
    將英文翻譯成中文（繁體）
    :param text: 英文句子
    :return: 中文翻譯結果
    """
    lines = text.split("\n")
    
    # 翻譯每行
    translated_lines = [translator.translate(line, src='en', dest='zh-tw').text for line in lines]
    
    # 將翻譯結果重新合併，使用換行符分隔
    translated_text = "\n".join(translated_lines)
    
    return translated_text

# 測試範例
if __name__ == "__main__":
    zh_example = "我喜歡研究人工智慧與加密貨幣。"
    en_example = "I enjoy researching artificial intelligence and cryptocurrency.\n"

    print("中文 → 英文：", translate_to_english(zh_example))
    print("英文 → 中文：", translate_to_chinese(en_example))
