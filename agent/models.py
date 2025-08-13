from django.db import models
from django.contrib.auth.models import User

class Questionnaire(models.Model):
    title = models.CharField(max_length=200, verbose_name="問卷名稱")

    def __str__(self):
        return self.title

class Question(models.Model):
    SINGLE_CHOICE = 'single'
    MULTIPLE_CHOICE = 'multiple'
    TEXT = 'text'

    QUESTION_TYPE_CHOICES = [
        (SINGLE_CHOICE, '單選'),
        (MULTIPLE_CHOICE, '多選'),
        (TEXT, '文字填答'),
    ]

    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name='questions', verbose_name="所屬問卷")
    order = models.PositiveIntegerField(verbose_name="題目排序")
    content = models.TextField(verbose_name="題目內容")
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPE_CHOICES, default=SINGLE_CHOICE, verbose_name="題目類型")

    def __str__(self):
        return f"{self.order}. {self.content[:50]}"

    class Meta:
        ordering = ['order']

class AnswerOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answer_options', verbose_name="所屬題目")
    content = models.CharField(max_length=200, verbose_name="答案選項")
    order = models.PositiveIntegerField(verbose_name="選項排序")
    score = models.IntegerField(default=0, verbose_name="風險分數")

    def __str__(self):
        return self.content

    class Meta:
        ordering = ['order']

class UserAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="使用者")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="題目")
    # 單選和多選的答案
    selected_options = models.ManyToManyField(AnswerOption, blank=True, verbose_name="選擇的答案")

    def __str__(self):
        return f"{self.user.username} - Q{self.question.order} 回答"

class UserQuestionnaireRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="使用者")
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, verbose_name="問卷")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="完成填寫時間")

    last_submitted_hash = models.CharField(max_length=64, null=True, blank=True)
    gpt_analysis_result = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} 填寫 {self.questionnaire.title}"
