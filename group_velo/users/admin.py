from django.conf import settings
from django.contrib import admin
from django.contrib.auth import decorators, get_user_model

from .models import EmergencyContact

User = get_user_model()

if settings.DJANGO_ADMIN_FORCE_ALLAUTH:
    # Force the `admin` sign in process to go through the `django-allauth` workflow:
    # https://django-allauth.readthedocs.io/en/stable/advanced.html#admin
    admin.site.login = decorators.login_required(admin.site.login)  # type: ignore[method-assign]

admin.site.register(User)
admin.site.register(EmergencyContact)
