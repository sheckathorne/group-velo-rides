from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path(
        "",
        views.NotificationsView.as_view(),
        name="notifications",
    ),
    path(
        "navbar_notifications/",
        login_required(views.get_navbar_notifications, login_url="/login"),
        name="get_navbar_notifications",
    ),
    path(
        "move_to_inbox/<str:notification_list>/",
        views.MoveNotificationsToInboxView.as_view(),
        name="unarchive_notification",
    ),
    path(
        "archived/",
        views.NotificationsArchivedView.as_view(),
        name="notifications_archived",
    ),
    path(
        "read/<str:notification_sqid>/",
        views.ReadNotificationView.as_view(),
        name="read_notification",
    ),
    path(
        "read_many/<str:notification_list>/",
        views.ReadManyNotificationsView.as_view(),
        name="read_many_notifications",
    ),
    path(
        "unread_many/<str:notification_list>/",
        views.UnreadManyNotificationsView.as_view(),
        name="unread_many_notifications",
    ),
    path(
        "archive_many/<str:notification_list>/",
        views.MoveNotificationsToArchiveView.as_view(),
        name="archive_many_notifications",
    ),
    path(
        "unread_notifications/<str:bubble_type>/",
        login_required(views.get_unread_notifications, login_url="/login"),
        name="unread_notifications",
    ),
    path("remove_alert_banner", views.remove_alert_banner, name="remove_alert_banner"),
]
