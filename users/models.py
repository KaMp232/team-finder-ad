from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import UserManager

SKILL_NAME_MAX_LENGTH = 124
USER_NAME_MAX_LENGTH = 124
USER_SURNAME_MAX_LENGTH = 124
USER_PHONE_MAX_LENGTH = 12
USER_ABOUT_MAX_LENGTH = 256


class Skill(models.Model):
    name = models.CharField(
        max_length=SKILL_NAME_MAX_LENGTH,
        unique=True,
        db_index=True,
    )

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


def avatar_upload_to(instance, filename):
    return f"avatars/user_{instance.pk or 'new'}_{filename}"


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=USER_NAME_MAX_LENGTH)
    surname = models.CharField(max_length=USER_SURNAME_MAX_LENGTH)
    avatar = models.ImageField(upload_to=avatar_upload_to, blank=True)
    phone = models.CharField(
        max_length=USER_PHONE_MAX_LENGTH,
        blank=True,
        null=True,
        unique=True,
    )
    github_url = models.URLField(blank=True)
    about = models.TextField(max_length=USER_ABOUT_MAX_LENGTH, blank=True)
    skills = models.ManyToManyField(Skill, blank=True, related_name="users")
    favorites = models.ManyToManyField(
        "projects.Project",
        blank=True,
        related_name="interested_users",
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ("name", "surname")

    class Meta:
        ordering = ("-date_joined", "-id")

    def __str__(self):
        return f"{self.name} {self.surname}".strip() or self.email
