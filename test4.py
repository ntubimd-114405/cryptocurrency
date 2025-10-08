import jieba
from rouge import Rouge

reference = "今天天氣真好，我們去公園散步吧。"
hypothesis = "今天天氣很好，我們去公園走走。"

# 中文斷詞
ref_tokens = " ".join(jieba.lcut(reference))
hyp_tokens = " ".join(jieba.lcut(hypothesis))

rouge = Rouge()
scores = rouge.get_scores(hyp_tokens, ref_tokens)
print(scores)
