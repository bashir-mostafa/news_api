from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = 'accounts'

    def ready(self):
        from django.db.utils import OperationalError, ProgrammingError
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            if not User.objects.filter(username='superadmin').exists():
                User.objects.create_superuser(
                    username='superadmin',
                    email='admin@admin.com',
                    password='Bashir7200!@@!'
                )
        except (OperationalError, ProgrammingError):
            pass


        