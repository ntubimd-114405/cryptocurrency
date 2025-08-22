# crypto_ai_agent/qa_agent.py

from typing import Optional
from django.contrib.auth.models import User

from .news_agent import run_news_agent
from .price_agent import run_price_agent
from .survey_agent import run_survey_agent
from .summarizer import summarize_all_individual

def create_qa_function(
    model_name: str = "mistral",
    embed_model: str = "mxbai-embed-large",
    db_path: str = "./vector_db/news",
    top_k: int = 5,
):
    def qa_func(question: str, user: Optional[User] = None) -> str:
        news_text = run_news_agent(question, db_path=db_path, embed_model=embed_model, top_k=top_k)
        price_text = run_price_agent(days=30)
        survey_text = run_survey_agent(user)
        
        answer = summarize_all_individual(
            question=question,
            news=news_text,
            price=price_text,
            survey=survey_text,
            model=model_name,
        )
        return answer
    return qa_func
