from io import BytesIO
from uuid import uuid4

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

from .managers import UserManager

SKILL_NAME_MAX_LENGTH = 124
USER_NAME_MAX_LENGTH = 124
USER_SURNAME_MAX_LENGTH = 124
USER_PHONE_MAX_LENGTH = 12
USER_ABOUT_MAX_LENGTH = 256
AVATAR_SIZE = 256
AVATAR_BACKGROUND = "#2F6FED"
AVATAR_FOREGROUND = "#FFFFFF"
AVATAR_IMAGE_FORMAT = "PNG"
AVATAR_FILE_EXTENSION = "png"


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


def build_default_avatar(initial):
    image = Image.new("RGB", (AVATAR_SIZE, AVATAR_SIZE), AVATAR_BACKGROUND)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=AVATAR_SIZE // 2)
    bbox = draw.textbbox((0, 0), initial, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    position = (
        (AVATAR_SIZE - text_width) / 2,
        (AVATAR_SIZE - text_height) / 2 - bbox[1],
    )
    draw.text(position, initial, fill=AVATAR_FOREGROUND, font=font)

    buffer = BytesIO()
    image.save(buffer, format=AVATAR_IMAGE_FORMAT)
    return ContentFile(buffer.getvalue())


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=USER_NAME_MAX_LENGTH)
    surname = models.CharField(max_length=USER_SURNAME_MAX_LENGTH)
    avatar = models.ImageField(upload_to=avatar_upload_to)
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

    def save(self, *args, **kwargs):
        if not self.avatar:
            source = self.name or self.email or "U"
            initial = source.strip()[:1].upper() or "U"
            filename = f"avatar_{uuid4()}.{AVATAR_FILE_EXTENSION}"
            self.avatar.save(filename, build_default_avatar(initial), save=False)
        super().save(*args, **kwargs)
