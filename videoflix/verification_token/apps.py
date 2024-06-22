from django.apps import AppConfig


class EmailVerificationConfig(AppConfig):
    name = 'verification_token'

    def ready(self):
        import verification_token.signals