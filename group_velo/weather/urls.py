from django.urls import path

from . import views

urlpatterns = [
    path("", views.weather_page, name="weather_page"),
    path("get-weather/", views.get_weather, name="get_weather"),
    path("task-status/", views.check_task_status, name="check_task_status"),
]
