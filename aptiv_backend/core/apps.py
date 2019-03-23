from django.apps import AppConfig


class CoreAppConfig(AppConfig):

    name = "aptiv_backend.core"
    verbose_name = "Site Core"

    # def ready(self):
    #     try:
    #         import users.signals  # noqa F401
    #     except ImportError:
    #         pass
