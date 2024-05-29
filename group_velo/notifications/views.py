from better_elided_pagination.paginators import BetterElidedPaginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.generic.base import TemplateView, View

from group_velo.notifications.decorators import can_read_notification_for_user
from group_velo.notifications.models import Notification
from group_velo.routes.urls import login_required
from group_velo.utils.mixins import SqidMixin


def append_notification_bubble_to_response(user):
    unread_count = user.unread_notifications().count()
    generic_notification_response = get_new_generic_bubble(unread_count)
    notification_count_bubble = get_notification_count_bubble(unread_count)
    return notification_count_bubble + generic_notification_response


@method_decorator(login_required(login_url="/login"), name="dispatch")
class NotificationBaseView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pagination"] = BetterElidedPaginator(self.request, self.get_notifications(), 10)
        return context

    def get_notifications(self):
        raise NotImplementedError("Subclasses must implement get_notifications method")


class NotificationsView(NotificationBaseView):
    template_name = "notifications/notifications.html"

    def get_notifications(self):
        return self.request.user.notifications()


class NotificationsArchivedView(NotificationBaseView):
    template_name = "notifications/archived_notifications.html"

    def get_notifications(self):
        return self.request.user.archived_notifications()


@method_decorator(login_required(login_url="/login"), name="dispatch")
@method_decorator(can_read_notification_for_user, name="dispatch")
class ReadNotificationView(SqidMixin, View):
    def post(self, request, *args, **kwargs):
        notification_id = self.decode_sqid(self.kwargs.get("notification_sqid", ""))
        notification = get_object_or_404(Notification, pk=notification_id).mark(read=True)
        response = render_to_string(
            "notifications/partials/notifications_table/_notifications_table_row.html",
            {"notification": notification},
        )

        response += append_notification_bubble_to_response(request.user)
        response += render_to_string(
            "notifications/modals/_notifications_detail_body.html",
            {"notification": notification},
        )

        return HttpResponse(response)

    def get(self, request, *args, **kwargs):
        return HttpResponse("")


@method_decorator(login_required(login_url="/login"), name="dispatch")
class ReadNotificationBase(View):
    def render_response(self):
        notifications = self.request.user.notifications()
        pagination = BetterElidedPaginator(self.request, notifications, 10)
        pagination.page_num = self.request.GET.get("page", 1)
        return render_to_string(
            "notifications/partials/_notifications_body.html",
            {
                "pagination": pagination,
            },
        )

    def mark_and_render_notification_group(self, notification_list, read=False):
        if len(notification_list) > 0:
            ids = notification_list.split(",")
            for id in ids:
                notification = get_object_or_404(Notification, pk=id)
                notification.mark(read=read)
            response = self.render_response()
            response += append_notification_bubble_to_response(self.request.user)
        else:
            response = self.render_response()
        return response

    def post(self, request, *args, notification_list=[], **kwargs):
        return HttpResponse(self.mark_and_render_notification_group(notification_list, read=self.read))

    def get(self, request, *args, **kwargs):
        return HttpResponse("")


class ReadManyNotificationsView(ReadNotificationBase):
    read = True


class UnreadManyNotificationsView(ReadNotificationBase):
    read = False


def get_unread_notifications(request, bubble_type):
    user = request.user
    template = ""
    unread_notifications_count = user.unread_notifications().count()

    oob = False
    notifications_exist = False

    if bubble_type == "generic":
        template = "notifications/partials/user/_generic_notification.html"
        if unread_notifications_count > 0:
            notifications_exist = True
    elif bubble_type == "specific":
        template = "notifications/partials/user/_notification_bubble.html"
        if unread_notifications_count > 0:
            notifications_exist = True

    response = render_to_string(
        template,
        {
            "notification_count": unread_notifications_count,
            "oob": oob,
            "notifications_exist": notifications_exist,
        },
    )

    return HttpResponse(response)


def render_notification(template, oob, notifications, specific_club=False):
    notifications_exist = True
    club_id = None

    if specific_club:
        club_id = notifications["pending_club_id"]

    response = render_to_string(
        template,
        {
            "oob": oob,
            "notifications_exist": notifications_exist,
            "notification_count": notifications,
            "club_id": club_id,
        },
    )

    return response


def get_navbar_notifications(request):
    user = request.user
    unread_notifications_count = user.unread_notifications().count()
    club_membership_requests = user.club_membership_request_count()
    club_membership_requests_count = user.club_membership_request_count().count()
    club_verification_request_count = user.club_verification_request_count()

    oob = True
    response = ""

    template = "notifications/partials/_navbar_notifications_caller.html"
    response = render_to_string(template)

    if unread_notifications_count > 0 or club_verification_request_count > 0:
        template = "notifications/partials/user/_generic_notification.html"
        response += render_notification(template, oob, unread_notifications_count)

        if unread_notifications_count > 0:
            template = "notifications/partials/user/_notification_bubble.html"
            response += render_notification(template, oob, unread_notifications_count)

        if club_verification_request_count > 0:
            template = "notifications/partials/verification/_notification_bubble.html"
            response += render_notification(template, oob, club_verification_request_count)

    if club_membership_requests_count > 0:
        template = "notifications/partials/club/_generic_notification.html"
        response += render_notification(template, oob, club_membership_requests_count)

        template = "notifications/partials/club/_notification_bubble.html"
        response += render_notification(template, oob, club_membership_requests_count)

        template = "notifications/partials/club/_generic_notification_club.html"
        for req in club_membership_requests:
            response += render_notification(template, oob, req, specific_club=True)

    return HttpResponse(response)


def get_new_generic_bubble(unread_count):
    notifications_exist = False
    if unread_count > 0:
        notifications_exist = True

    response = render_to_string(
        "notifications/partials/user/_generic_notification.html",
        {"oob": True, "notifications_exist": notifications_exist},
    )

    return response


def get_notification_count_bubble(unread_count):
    notifications_exist = False
    if unread_count > 0:
        notifications_exist = True

    response = render_to_string(
        "notifications/partials/user/_notification_bubble.html",
        {
            "oob": True,
            "notifications_exist": notifications_exist,
            "notification_count": unread_count,
        },
    )
    return response


@method_decorator(login_required(login_url="/login"), name="dispatch")
class MoveBetweenInboxAndArchiveBase(View):
    def render_template(self, archive):
        pagination = BetterElidedPaginator(self.request, self.notifications, 10)
        pagination.page_num = self.request.GET.get("page", 1)

        return render_to_string(
            self.template,
            {
                "pagination": pagination,
            },
        )

    def archive_notification_group(self, notification_list, archive=False):
        if archive:
            self.notifications = self.request.user.notifications()
            self.template = "notifications/partials/_notifications_body.html"
        else:
            self.notifications = self.request.user.archived_notifications()
            self.template = "notifications/partials/_archived_notifications_body.html"

        if len(notification_list) > 0:
            ids = notification_list.split(",")
            for id in ids:
                notification = get_object_or_404(Notification, pk=id)
                notification.archive(archive=archive)

            response = self.render_template(archive)
        else:
            response = self.render_template(archive)
        response += append_notification_bubble_to_response(self.request.user)

        return response

    def post(self, request, *args, notification_list=[], **kwargs):
        return HttpResponse(self.archive_notification_group(notification_list, archive=self.archive))

    def get(self, request, *args, **kwargs):
        return HttpResponse("")


class MoveNotificationsToInboxView(MoveBetweenInboxAndArchiveBase):
    archive = False


class MoveNotificationsToArchiveView(MoveBetweenInboxAndArchiveBase):
    archive = True


def remove_alert_banner(request):
    return HttpResponse("<div id='response-alert'></div>")
