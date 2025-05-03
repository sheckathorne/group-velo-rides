# ruff: noqa
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views import defaults as default_views
from django.views.generic import TemplateView

import group_velo.users.views as views

urlpatterns = [
    path("about/", TemplateView.as_view(template_name="pages/about.html"), name="about"),
    path("", views.home, name="home"),
    path(settings.ADMIN_URL, admin.site.urls),
    path("", include("group_velo.users.urls", namespace="users")),
    path(
        "notifications/",
        include("group_velo.notifications.urls", namespace="notifications"),
    ),
    path("events/", include("group_velo.events.urls", namespace="events")),
    path("clubs/", include("group_velo.clubs.urls", namespace="clubs")),
    path("routes/", include("group_velo.routes.urls", namespace="routes")),
    path("weather/", include("group_velo.routes.urls", namespace="weather")),
    path("accounts/", include("allauth.urls")),
    path("initials-avatar/", include("django_initials_avatar.urls")),
    path("unicorn/", include("django_unicorn.urls")),
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
]


if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
