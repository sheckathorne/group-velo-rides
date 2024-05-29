from django.contrib import admin

from .models import Route, UserRoute

admin.site.register(Route)
admin.site.register(UserRoute)
