from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "group_velo.users"
    verbose_name = _("Users")

    def ready(self):
        try:
            import group_velo.users.signals  # noqa: F401
        except ImportError:
            pass
