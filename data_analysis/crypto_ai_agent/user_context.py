# crypto_ai_agent/user_context.py

from agent.models import UserQuestionnaireRecord, UserAnswer
from django.contrib.auth.models import User

def get_user_questionnaire_context(user: User, max_items: int = 10) -> str:
    records = (
        UserQuestionnaireRecord.objects
        .filter(user=user)
        .order_by("-completed_at")[:max_items]
    )

    context_lines = []
    for record in records:
        context_lines.append(f"\n🧾 問卷：{record.questionnaire.title}")
        user_answers = (
            UserAnswer.objects
            .filter(user=user, question__questionnaire=record.questionnaire)
            .select_related("question")
            .prefetch_related("selected_options")
        )
        for ans in user_answers:
            q = ans.question
            selected = [opt.content for opt in ans.selected_options.all()]
            selected_str = ", ".join(selected) if selected else "（未填答）"
            context_lines.append(f"Q{q.order}. {q.content}\n→ 回答：{selected_str}")

    return "\n".join(context_lines)
