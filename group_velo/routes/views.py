from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.urls.base import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from sqids.sqids import Sqids

from config.settings.base import SQIDS_ALPHABET, SQIDS_MIN_LEN
from group_velo.data.choices import MemberType
from group_velo.routes.forms import RouteForm
from group_velo.routes.models import Route
from group_velo.routes.urls import can_modify_route
from group_velo.utils.mixins import SqidMixin


@method_decorator(login_required(login_url="/login"), name="dispatch")
class MyRoutesView(ListView):
    template_name = "routes/my_routes_scaffold.html"
    context_object_name = "routes"

    def get_queryset(self):
        return self.request.user.routes()


@method_decorator(login_required(login_url="/login"), name="dispatch")
class BaseRouteView(LoginRequiredMixin, SuccessMessageMixin):
    model = Route
    success_url = reverse_lazy("routes:my_routes")

    def get_object(self, queryset=None):
        route_id = self.decode_sqid(self.kwargs.get("route_sqid", ""))
        return get_object_or_404(self.model, id=route_id)


class BaseModifyRouteView(SuccessMessageMixin):
    form_class = RouteForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user_clubs"] = self.request.user.route_create_clubs(MemberType.RouteContributor)
        return kwargs


@method_decorator(can_modify_route, name="dispatch")
class DeleteRouteView(BaseRouteView, SqidMixin, DeleteView):
    success_message = "Successfully deleted route."


class CreateRouteView(BaseRouteView, BaseModifyRouteView, SqidMixin, CreateView):
    template_name = "routes/create_route.html"
    success_message = "Successfully created new route."

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.club = form.cleaned_data["club"]
        obj.created_by = self.request.user
        obj.save()
        return super().form_valid(form)


@method_decorator(can_modify_route, name="dispatch")
class EditRouteView(BaseRouteView, BaseModifyRouteView, SqidMixin, UpdateView):
    success_message = "Successfully updated route."


def get_edit_form(request, route_sqid):
    sqids = Sqids(alphabet=SQIDS_ALPHABET, min_length=SQIDS_MIN_LEN)
    route_id = sqids.decode(route_sqid)[0]
    route = get_object_or_404(Route, id=route_id)
    template = "routes/modals/edit_route/_body.html"
    form_action = reverse("routes:edit_route", kwargs={"route_sqid": route_sqid})
    user = request.user
    user_clubs = user.route_create_clubs(MemberType.RouteContributor)
    form = RouteForm(user_clubs, instance=route)
    return HttpResponse(render_to_string(template, {"form_action": form_action, "form": form}, request=request))


def get_delete_form(request, route_sqid):
    template = "routes/modals/delete_route/_body.html"
    form_action = reverse("routes:delete_route", kwargs={"route_sqid": route_sqid})
    return HttpResponse(render_to_string(template, {"form_action": form_action}, request=request))


def get_blank_edit_route_form(request):
    template = "routes/modals/edit_route/_blank_body.html"
    return HttpResponse(render_to_string(template))


def get_blank_delete_route_form(request):
    template = "routes/modals/delete_route/_blank_body.html"
    return HttpResponse(render_to_string(template))
