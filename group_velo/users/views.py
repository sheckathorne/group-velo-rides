import os

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.generic import TemplateView
from sqids.sqids import Sqids

from config.settings.base import SQIDS_ALPHABET, SQIDS_MIN_LEN
from group_velo.users.forms import (
    EmailPartialForm,
    EmergencyContactForm,
    NamePartialForm,
    PasswordConfirmPartialForm,
    PasswordPartialForm,
    PasswordResetForm,
    ResendEmailForm,
    SetPasswordForm,
    UserLoginForm,
    UsernamePartialForm,
    UserProfileForm,
    UserRegistrationForm,
    ZipCodePartialForm,
)
from group_velo.users.models import EmergencyContact

from .decorators import user_not_authenticated
from .tokens import account_activation_token


@login_required(login_url="/login")
def home(request):
    return HttpResponseRedirect(reverse("events:my_rides"))


def activate(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()

        messages.success(
            request,
            "Your email has been confirmed, you may now log in to your account.",
            extra_tags="timeout-5000",
        )
        return redirect(reverse("users:login"))
    else:
        messages.error(request, "Activation link is invalid!")

    return redirect(reverse("home"))


def activate_email(request, user, to_email):
    mail_subject = "Activate your user account."
    message = render_to_string(
        "users/activate_account.html",
        {
            "user": user.username,
            "domain": get_current_site(request).domain,
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": account_activation_token.make_token(user),
            "protocol": "https" if request.is_secure() else "http",
        },
    )
    email = EmailMessage(mail_subject, message, to=[to_email])
    if email.send():
        messages.success(
            request,
            f"Confirmation email sent to <b>{to_email}</b>. Please go to your inbox and click on "
            f"the activation link to confirm and complete the registration. <b>Note:</b> Check "
            f"your spam folder.",
        )
    else:
        messages.error(
            request,
            f"There was a problem sending the confirmation email to {to_email}, " f"check if you typed it correctly.",
        )


@user_not_authenticated
def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            activate_email(request, user, form.cleaned_data.get("email"))
            return redirect(reverse("users:await_confirmation"))

        else:
            for error in list(form.errors.values()):
                messages.error(request, error)

    else:
        form = UserRegistrationForm()

    return render(request=request, template_name="users/register.html", context={"form": form})


def await_confirmation(request):
    if request.method == "POST":
        form = ResendEmailForm(request.POST)
        if form.is_valid():
            User = get_user_model()
            email = form.cleaned_data.get("email")
            user = User.objects.get(email=email)
            activate_email(request, user, form.cleaned_data.get("email"))
            return redirect(reverse("users:await_confirmation"))
        else:
            for error in list(form.errors.values()):
                messages.error(request, error)
    else:
        form = ResendEmailForm()

    return render(
        request=request,
        template_name="users/await_confirmation.html",
        context={"form": form},
    )


@login_required
def custom_logout(request):
    logout(request)
    messages.info(request, "Logged out successfully!", extra_tags="timeout-5000")
    return redirect(reverse("home"))


def custom_login(request):
    if request.user.is_authenticated:
        return redirect(reverse("home"))

    if request.method == "POST":
        form = UserLoginForm(request=request, data=request.POST)
        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )
            if user is not None:
                login(request, user)
                messages.success(request, "Logged in successfully!", extra_tags="timeout-5000")
                return redirect(request.GET.get("next", "home"))
                # return redirect(reverse("home"))
            else:
                for error in list(form.errors.values()):
                    messages.error(request, error)
        else:
            for key, error in list(form.errors.items()):
                if key == "captcha" and error[0] == "This field is required.":
                    messages.error(request, "You must pass the reCAPTCHA test")
                    continue
                messages.error(request, error)

    form = UserLoginForm()

    return render(request=request, template_name="users/login.html", context={"form": form})


@login_required
def change_password(request):
    user = request.user
    if request.method == "POST":
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your password has been changed", extra_tags="timeout-5000")
            return redirect(reverse("users:login"))
        else:
            for error in list(form.errors.values()):
                messages.error(request, error)
    form = SetPasswordForm(user)
    return render(request, "users/password_reset_confirmation.html", {"form": form})


def reset_password_request(request):
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            user_email = form.cleaned_data["email"]
            associated_user = get_user_model().objects.filter(Q(email=user_email)).first()
            if associated_user:
                subject = "Password reset request"
                message = render_to_string(
                    "users/reset_password_email.html",
                    {
                        "user": associated_user,
                        "domain": get_current_site(request).domain,
                        "uid": urlsafe_base64_encode(force_bytes(associated_user.pk)),
                        "token": account_activation_token.make_token(associated_user),
                        "protocol": "https" if request.is_secure() else "http",
                    },
                )
                email = EmailMessage(subject, message, to=[associated_user.email])
                if email.send():
                    messages.success(
                        request,
                        """
                                     <h2>Password reset sent</h2><hr>
                                     <p>
                                        We've sent an email with password reset instructions to """
                        + user_email
                        + """ if
                                        <br>If you don't receive an email, please make sure you've entered the address
                                        associated with your account, and also make sure to check your spam folder.
                                     </p>""",
                    )
                else:
                    messages.error(
                        request,
                        "There was a problem sending the password reset email, please try again.",
                    )
            return redirect(reverse("home"))

        for key, error in list(form.errors.items()):
            if key == "captcha" and error[0] == "This field is required.":
                messages.error(request, "You must pass the reCAPTCHA test")
                continue
    form = PasswordResetForm()
    return render(
        request=request,
        template_name="users/password_reset.html",
        context={"form": form},
    )


def reset_password_confirm(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except ObjectDoesNotExist:
        user = None

    if user and account_activation_token.check_token(user, token):
        if request.method == "POST":
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(
                    request,
                    "Your password has been set. You may go ahead and <b>log in</b> now.",
                    extra_tags="timeout-5000",
                )
                return redirect(reverse("home"))
            else:
                for error in list(form.errors.values()):
                    messages.error(request, error)

        form = SetPasswordForm(user)
        return render(request, "users/password_reset_confirmation.html", {"form": form})
    else:
        messages.error(request, "Link is expired.")

    messages.error(request, "Something went wrong, redirecting back to homepage.")
    return redirect(reverse("home"))


def signup_redirect(request):
    messages.error(request, "Something wrong here, it may be that you already have account!")
    return redirect(reverse("home"))


class UserProfile(TemplateView):
    def get(self, *args, **kwargs):
        user = self.request.user
        emergency_contacts = user.emergency_contacts()
        form = UserProfileForm(instance=user)

        return render(
            self.request,
            "users/profile/user_profile.html",
            {"form": form, "emergency_contacts": emergency_contacts},
        )

    @staticmethod
    def post(request):
        user = request.user

        if request.method == "POST":
            form = UserProfileForm(request.POST, request.FILES, instance=user)
            old_image = user.avatar
            if form.is_valid():
                if old_image:
                    image_path = get_user_model().image_upload_to(user, instance=old_image.path)
                    if os.path.exists(image_path) and old_image.url is not None:
                        os.remove(image_path)

                form.save()
                messages.success(
                    request,
                    "Successfully updated your user profile.",
                    extra_tags="timeout-5000",
                )
                return HttpResponseRedirect(reverse("users:edit_profile"))
            else:
                for error in list(form.errors.values()):
                    messages.error(request, error)

        form = UserProfileForm(request.POST, request.FILES, instance=user)
        return render(
            request=request,
            template_name="users/profile/user_profile.html",
            context={"form": form},
        )


def emergency_contact_form(request):
    ec_form = EmergencyContactForm()
    context = {"ec_form": ec_form}
    response = render(request, "users/profile/create_emergency_contact_form.html", context)
    response["HX-Trigger-After-Swap"] = "contactDeleteHideFormButton"
    return response


def create_emergency_contact(request):
    user = request.user
    emergency_contacts = user.emergency_contacts()
    form = UserProfileForm(instance=user)
    ec_form = EmergencyContactForm(request.POST or None, user=request.user)

    if request.method == "POST":
        form_data = request.POST.copy()
        form_data["phone_number"] = "+1 " + form_data["phone_number"]
        ec_form = EmergencyContactForm(form_data)
        if ec_form.is_valid():
            emergency_contact = ec_form.save(commit=False)
            emergency_contact.contact_for = user
            emergency_contact.save()

            emergency_contacts = user.emergency_contacts()
            rendered_template = render_to_string(
                "users/profile/emergency_contacts_list.html",
                {
                    "emergency_contacts": emergency_contacts,
                    "request": request,
                    "allow_delete": True,
                },
                request=request,
            )

            response = HttpResponse(rendered_template)
            response["HX-Trigger-After-Swap"] = "contactDeleteShowFormButton"
            return response
        else:
            rendered_contacts = render_to_string(
                "events/modals/emergency_contacts_list.html",
                {
                    "emergency_contacts": emergency_contacts,
                    "request": request,
                    "allow_delete": True,
                },
                request=request,
            )

            rendered_form = render_to_string(
                "users/profile/create_emergency_contact_form.html",
                {"ec_form": ec_form},
                request=request,
            )

            response = HttpResponse(f"{rendered_contacts} {rendered_form}")
            response["HX-Trigger-After-Swap"] = "contactDelete"
            return response

    return render(
        request,
        "users/user_profile.html",
        context={
            "form": form,
            "ec_form": ec_form,
            "emergency_contacts": emergency_contacts,
        },
    )


def delete_emergency_contact(request, contact_sqid):
    sqids = Sqids(alphabet=SQIDS_ALPHABET, min_length=SQIDS_MIN_LEN)
    if request.method == "POST":
        contact_id = sqids.decode(contact_sqid)[0]
        emergency_contact = get_object_or_404(EmergencyContact, pk=contact_id)
        emergency_contact.delete()
        response = HttpResponse("")
        response["HX-Trigger-After-Swap"] = "contactDelete"
        return response


def get_blank_delete_emergency_contact_form(request):
    return HttpResponse(render_to_string("users/profile/modals/delete_emergency_contact/_blank_body.html"))


def get_delete_emergency_contact_form(request, contact_sqid):
    sqids = Sqids(alphabet=SQIDS_ALPHABET, min_length=SQIDS_MIN_LEN)
    contact_id = sqids.decode(contact_sqid)[0]
    emergency_contact = get_object_or_404(EmergencyContact, id=contact_id)
    template = "users/profile/modals/delete_emergency_contact/_body.html"
    form_action = reverse("users:delete_emergency_contact", kwargs={"contact_sqid": contact_sqid})
    modal_body = f"Are you sure you want to remove {emergency_contact.name} from your emergency contacts?"
    target = f"#emergency-contact-row-{contact_sqid}"
    return HttpResponse(
        render_to_string(
            template,
            {"form_action": form_action, "modal_body": modal_body, "target": target},
            request=request,
        )
    )


def render_registration_field(request, template, error_message, value, swap_oob=False, valid=True):
    response = render_to_string(
        template,
        {
            "error_message": error_message,
            "value": value,
            "swap_oob": swap_oob,
            "valid": valid,
        },
        request=request,
    )
    return response


def register_check_email(request):
    if request.method == "POST":
        email = request.POST.get("email")
        User = get_user_model()
        user_email_exists = User.objects.filter(email=email).exists()
        template = "users/check_form_fields/email.html"
        valid = True
        error_message = ""

        if user_email_exists:
            error_message = "Email is already in use"
            valid = False
        else:
            form = EmailPartialForm(request.POST)
            if not form.is_valid():
                error_message = " ".join([" ".join(x for x in lst) for lst in list(form.errors.values())])
                valid = False

        return HttpResponse(render_registration_field(request, template, error_message, email, valid=valid))


def register_check_username(request):
    if request.method == "POST":
        username = request.POST.get("username")
        User = get_user_model()
        user_username_exists = User.objects.filter(username=username).exists()
        template = "users/check_form_fields/username.html"
        valid = True
        error_message = ""

        if user_username_exists:
            error_message = "Username is already in use"
            valid = False
        else:
            form = UsernamePartialForm(request.POST)
            if not form.is_valid():
                error_message = " ".join([" ".join(x for x in lst) for lst in list(form.errors.values())])
                valid = False

        return HttpResponse(render_registration_field(request, template, error_message, username, valid=valid))


def register_check_name(request):
    if request.method == "POST":
        name = request.POST.get("name")
        template = "users/check_form_fields/name.html"
        valid = True
        error_message = ""

        form = NamePartialForm(request.POST)
        if not form.is_valid():
            error_message = " ".join([" ".join(x for x in lst) for lst in list(form.errors.values())])
            valid = False

        return HttpResponse(render_registration_field(request, template, error_message, name, valid=valid))


def register_check_zip_code(request):
    if request.method == "POST":
        zip_code = request.POST.get("zip_code")
        form = ZipCodePartialForm(request.POST)
        template = "users/check_form_fields/zip_code.html"
        valid = True
        error_message = ""

        if not form.is_valid():
            error_message = " ".join([" ".join(x for x in lst) for lst in list(form.errors.values())])
            valid = False

        return HttpResponse(render_registration_field(request, template, error_message, zip_code, valid=valid))


def register_check_password(request):
    if request.method == "POST":
        password = request.POST.get("password1")
        password_confirm = request.POST.get("password2")

        # check if the first password is good
        error_message = ""
        valid = True
        template = "users/check_form_fields/password.html"

        form = PasswordPartialForm({"password": password})
        if not form.is_valid():
            error_message = " ".join([" ".join(x for x in lst) for lst in list(form.errors.values())])
            valid = False

        response = render_registration_field(request, template, error_message, password, valid=valid)

        # check if password2 matches password1 on password1 change
        if password_confirm:
            error_message = ""
            valid = True
            template = "users/check_form_fields/password_confirm.html"

            form = PasswordConfirmPartialForm(request.POST)
            if not form.is_valid():
                error_message = " ".join([" ".join(x for x in lst) for lst in list(form.errors.values())])
                valid = False

            response = response + render_registration_field(
                request,
                template,
                error_message,
                password_confirm,
                swap_oob=True,
                valid=valid,
            )

        return HttpResponse(response)


def register_check_password_confirm(request):
    if request.method == "POST":
        password_confirmation = request.POST.get("password2")
        password_confirm_form = PasswordConfirmPartialForm(request.POST)
        error_message = ""
        valid = True
        template = "users/check_form_fields/password_confirm.html"

        if not password_confirm_form.is_valid():
            error_message = " ".join([" ".join(x for x in lst) for lst in list(password_confirm_form.errors.values())])
            valid = False

        return HttpResponse(
            render_registration_field(request, template, error_message, password_confirmation, valid=valid)
        )
