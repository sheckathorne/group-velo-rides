from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Checkbox
from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Field, Layout
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordResetForm as PassResetForm,
    SetPasswordForm as SetPassForm,
    UserCreationForm,
)
from django.core.exceptions import ValidationError
from django.forms import NumberInput
from django.urls import reverse
from image_uploader_widget.widgets import ImageUploaderWidget

from group_velo.users.models import EmergencyContact
from group_velo.utils.utils import css_container, form_row_new


class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = [
            "name",
            "username",
            "email",
            "zip_code",
            "password1",
            "password2",
        ]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class UserPartialForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ["name", "username", "email", "zip_code", "password"]


class UserFieldForm(UserPartialForm):
    def __init__(self, *args, **kwargs):
        field_name = kwargs.pop("field_name", None)
        super().__init__(*args, **kwargs)
        for field in self.Meta.fields:
            if field != field_name:
                self.fields.pop(field)


class PasswordConfirmPartialForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ["password1", "password2"]


class UserLoginForm(AuthenticationForm):
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox())
    username = forms.CharField(label="Username", max_length=255)
    password = forms.CharField(label="Password", widget=forms.PasswordInput)


class ResendEmailForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=100)

    def __init__(self, *args, **kwargs):
        css = css_container()
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.css_container = css
        self.helper.layout = Layout(
            Field(
                "email",
                css_class="shadow-lg",
                wrapper_class="mb-4 lg:w-1/2 md:w-2/3 w-full",
                placeholder="Email",
            ),
        )


class SetPasswordForm(SetPassForm):
    def __init__(self, *args, **kwargs):
        css = css_container()
        super().__init__(*args, **kwargs)
        self.fields["new_password2"].label = "Confirm Password"

        self.helper = FormHelper(self)
        self.helper.css_container = css
        self.helper.layout = Layout(
            Field(
                "new_password1",
                css_class="shadow-lg",
                wrapper_class="mb-4",
                placeholder="Enter New Password",
            ),
            Field(
                "new_password2",
                css_class="shadow-lg",
                wrapper_class="mb-4 mt-4",
                placeholder="Re-enter New Password",
            ),
            StrictButton(
                "Change Password",
                value="submit",
                type="submit",
                css_class="w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold py-2 px-4 "
                "rounded shadow-lg mb-4",
            ),
        )

    class Meta:
        model = get_user_model()
        fields = ["new_password1", "new_password2"]


class PasswordResetForm(PassResetForm):
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox())

    def __init__(self, *args, **kwargs):
        css = css_container()
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.css_container = css
        self.helper.layout = Layout(
            Field(
                "email",
                css_class="shadow-lg",
                wrapper_class="mb-4 mt-4",
                placeholder="Enter email",
            ),
            Field(
                "captcha",
                css_class="shadow-lg rounded-lg",
                wrapper_class="mb-4",
                placeholder="Enter Recaptcha",
            ),
            StrictButton(
                "Send Email",
                value="submit",
                type="submit",
                css_class="w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold py-2 px-4 "
                "rounded shadow-lg mb-4",
            ),
        )


class UserProfileForm(forms.ModelForm):
    name = forms.CharField(max_length=50)

    class Meta:
        model = get_user_model()
        fields = ["name", "zip_code", "avatar", "about"]

        widgets = {
            "avatar": ImageUploaderWidget(),
            "zip_code": NumberInput(),
        }

    def __init__(self, *args, **kwargs):
        row_padding = "pb-2"

        self.submit_text = kwargs.pop("submit_text", "Submit")
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.css_container = css_container()
        self.helper.layout = Layout(
            Div(
                Div(
                    form_row_new(
                        Field("avatar", wrapper_class="w-full shadow-lg"),
                        padding_bottom=row_padding,
                    ),
                    form_row_new(
                        Field("name", wrapper_class="w-full shadow-lg"),
                        padding_bottom=row_padding,
                    ),
                    form_row_new(
                        Field("zip_code", wrapper_class="w-full shadow-lg"),
                        padding_bottom=row_padding,
                    ),
                    css_class="w-full",
                ),
                Div(
                    form_row_new(
                        Field(
                            "about",
                            wrapper_class="w-full shadow-lg",
                            css_class="h-auto",
                        ),
                        padding_bottom=row_padding,
                    ),
                    css_class="w-full h-auto",
                ),
                css_class="w-full grid xl:grid-cols-3 md:grid-cols-2 grid-cols-1 gap-2",
            )
        )


class EmergencyContactForm(forms.ModelForm):
    class Meta:
        model = EmergencyContact
        fields = ["name", "phone_number", "relationship"]

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        self.submit_text = kwargs.pop("submit_text", "Submit")
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.css_container = css_container()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Field("name"),
                Field(
                    "phone_number",
                    id="emergency_contact_create_phone_number",
                    css_class="w-full shadow textinput border rounded border-gray-300 focus:outline-none "
                    "dark:bg-gray-700 appearance-none dark:text-gray-200 w-full dark:border-gray-500 "
                    "text-gray-700 shadow px-4 leading-normal block py-2 bg-white",
                    label_class="dark:text-gray-200",
                    x_mask="(999) 999-9999",
                ),
                Field("relationship"),
                css_class="grid gap-2 grid-cols-3 pb-2 w-full xl:w-2/3",
            ),
            Div(
                Div(
                    HTML(
                        f'<button class ="w-full btn-primary-color" '
                        f'hx-post="{reverse("users:create_emergency_contact")}" '
                        f'hx-target="#emergency-contact-list" '
                        f'hx-swap="innerHTML">Save Contact</button>'
                    ),
                    css_class="w-full shadow-lg xl:col-span-1 sm:col-span-2 col-span-3",
                ),
                css_class="grid grid-cols-3 gap-2",
            ),
        )

    def clean(self):
        user = self.user
        if EmergencyContact.objects.filter(contact_for=user).count() >= 4:
            raise ValidationError("You may have a maximum of four emergency contacts")
