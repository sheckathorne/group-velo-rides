from django.contrib import admin

from group_velo.weather.models import WeatherForecastDay, WeatherForecastHour

admin.site.register(WeatherForecastDay)
admin.site.register(WeatherForecastHour)
