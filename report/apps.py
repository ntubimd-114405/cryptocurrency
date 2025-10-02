from django.apps import AppConfig


class ReportConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'report'

    def ready(self):
        from data_analysis.crypto_ai_agent.news_agent import initialize_global_store
        initialize_global_store()


