from django.urls import path

from . import views

app_name = "weather"

urlpatterns = [
    path("task-status/<str:task_id>/", views.check_task_status, name="check_task_status"),
]
