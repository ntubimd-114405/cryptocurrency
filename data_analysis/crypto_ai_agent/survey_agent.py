# crypto_ai_agent/survey_agent.py

from .user_context import get_user_questionnaire_context
from django.contrib.auth.models import User

def run_survey_agent(user: User) -> str:
    if not user:
        return "（無使用者背景資料）"
    return get_user_questionnaire_context(user)
