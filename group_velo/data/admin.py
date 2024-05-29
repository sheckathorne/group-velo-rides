from django.contrib import admin

from .models import NavBarItem, ZipCodeCoordinate

admin.site.register(ZipCodeCoordinate)
admin.site.register(NavBarItem)
