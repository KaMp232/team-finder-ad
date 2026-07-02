from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordChangeForm

from .models import User
from .utils import PHONE_RE, normalize_phone, validate_github_url

PASSWORD_WIDGET_ATTRS = {"autocomplete": "current-password"}
NEW_PASSWORD_WIDGET_ATTRS = {"autocomplete": "new-password"}
EMAIL_WIDGET_ATTRS = {"autocomplete": "email"}
NAME_WIDGET_ATTRS = {"autocomplete": "given-name"}
SURNAME_WIDGET_ATTRS = {"autocomplete": "family-name"}
PHONE_WIDGET_ATTRS = {"autocomplete": "tel"}
GITHUB_WIDGET_ATTRS = {"placeholder": "https://github.com/username"}
ABOUT_WIDGET_ATTRS = {"rows": 4}
PHONE_REQUIRED_MESSAGE = "Enter a phone number."
PHONE_INVALID_MESSAGE = "Phone must start with +7 or 8 and contain 11 digits."
PHONE_DUPLICATE_MESSAGE = "User with this phone already exists."
LOGIN_INVALID_MESSAGE = "Invalid email or password."


class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs=NEW_PASSWORD_WIDGET_ATTRS),
    )

    class Meta:
        model = User
        fields = ("name", "surname", "email", "password")
        widgets = {
            "name": forms.TextInput(attrs=NAME_WIDGET_ATTRS),
            "surname": forms.TextInput(attrs=SURNAME_WIDGET_ATTRS),
            "email": forms.EmailInput(attrs=EMAIL_WIDGET_ATTRS),
        }

    def save(self, commit=True):
        password = self.cleaned_data.pop("password")
        user = User(**self.cleaned_data)
        user.set_password(password)
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs=EMAIL_WIDGET_ATTRS))
    password = forms.CharField(widget=forms.PasswordInput(attrs=PASSWORD_WIDGET_ATTRS))

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.user = None

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")
        if email and password:
            self.user = authenticate(
                self.request,
                username=email,
                password=password,
            )
            if self.user is None:
                raise forms.ValidationError(LOGIN_INVALID_MESSAGE)
        return cleaned_data


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("avatar", "name", "surname", "about", "phone", "github_url")
        widgets = {
            "name": forms.TextInput(attrs=NAME_WIDGET_ATTRS),
            "surname": forms.TextInput(attrs=SURNAME_WIDGET_ATTRS),
            "about": forms.Textarea(attrs=ABOUT_WIDGET_ATTRS),
            "phone": forms.TextInput(attrs=PHONE_WIDGET_ATTRS),
            "github_url": forms.URLInput(attrs=GITHUB_WIDGET_ATTRS),
        }

    def clean_phone(self):
        phone = normalize_phone(self.cleaned_data.get("phone"))
        if not phone:
            return phone
        if not PHONE_RE.match(phone):
            raise forms.ValidationError(PHONE_INVALID_MESSAGE)
        users = User.objects.filter(phone=phone)
        if self.instance.pk:
            users = users.exclude(pk=self.instance.pk)
        if users.exists():
            raise forms.ValidationError(PHONE_DUPLICATE_MESSAGE)
        return phone

    def clean_github_url(self):
        github_url = self.cleaned_data.get("github_url")
        validate_github_url(github_url)
        return github_url


class UserPasswordChangeForm(PasswordChangeForm):
    pass
