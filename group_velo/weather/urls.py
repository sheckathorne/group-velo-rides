from django.urls import path

from . import views

urlpatterns = [
    path("task-status/", views.check_task_status, name="check_task_status"),
]
