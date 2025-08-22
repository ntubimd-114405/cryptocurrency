# agent/knowledge_data.py
from langchain_core.documents import Document

def get_knowledge_documents():
    return [
        # 📌 風險屬性配置建議（你原本的）
        Document(
            page_content="保守型投資人傾向於資產穩定、低波動，建議配置 70% 穩定幣（如 USDT、USDC）、20% 主流幣（如 BTC、ETH）、10% 成長型幣（如 SOL、AVAX）。",
            metadata={"id": "risk_conservative"}
        ),
        Document(
            page_content="穩健型投資人可接受中等風險與回報，建議配置 40% 穩定幣、40% 主流幣、20% 成長幣。",
            metadata={"id": "risk_moderate"}
        ),
        Document(
            page_content="積極型投資人尋求高回報，建議配置 20% 穩定幣、40% 主流幣、30% 成長幣、10% 迷因幣（如 DOGE、PEPE）。",
            metadata={"id": "risk_aggressive"}
        ),

        # 📌 幣種說明（你原本的）
        Document(
            page_content="主流幣如 BTC、ETH 是市場市值最大、最穩定的加密貨幣，適合長期持有。",
            metadata={"id": "coin_mainstream"}
        ),
        Document(
            page_content="穩定幣如 USDT、USDC 與美元掛鉤，適合用來避險或資金停泊。",
            metadata={"id": "coin_stable"}
        ),
        Document(
            page_content="成長幣如 SOL、AVAX 是新興公鏈或應用平台，具有發展潛力，但波動較高。",
            metadata={"id": "coin_growth"}
        ),

        # 📌 幣種分類（coin_categories.txt）
        Document(
            page_content="主流幣：BTC（比特幣）、ETH（以太幣）\n成長幣：SOL（Solana）、AVAX（Avalanche）、APT、ARB\n迷因幣：DOGE、SHIB、PEPE、FLOKI\n穩定幣：USDT、USDC、DAI\n其他幣：TON、ICP、WLD、MASK",
            metadata={"id": "coin_categories"}
        ),

        # 📌 加密貨幣風險因素（risk_factors.txt）
        Document(
            page_content="影響加密貨幣風險的主要因素包括：價格波動率、市值大小、項目成熟度、社群活動、監管風險等。\n\n主流幣市值高、流通穩定、風險低。迷因幣波動大、缺乏實質應用，風險高。",
            metadata={"id": "risk_factors"}
        ),

        # 📌 投資人風險屬性描述（risk_profile_description.txt）
        Document(
            page_content="保守型投資者：風險承受度低，追求資產穩定，偏好不虧損勝於高報酬。\n\n穩健型投資者：接受中等風險與報酬，願意部分資產波動。\n\n積極型投資者：風險接受度高，追求高報酬，願意承擔虧損風險。",
            metadata={"id": "risk_profile_description"}
        ),

        # 📌 各類投資人建議配置（risk_profile_recommendation.txt）
        Document(
            page_content="保守型投資人：建議配置為 60% 穩定幣（如 USDT、USDC）、30% 主流幣（如 BTC、ETH）、10% 成長幣（如 SOL、AVAX）\n\n穩健型投資人：建議配置為 30% 穩定幣、40% 主流幣、20% 成長幣、10% 迷因幣（如 DOGE、SHIB）\n\n積極型投資人：建議配置為 20% 主流幣、30% 成長幣、30% 迷因幣、20% 其他高風險幣種（如 PEPE、FLOKI）",
            metadata={"id": "risk_profile_recommendation"}
        ),
    ]
