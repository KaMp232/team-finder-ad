from io import BytesIO
from uuid import uuid4

from django.contrib.auth.models import AbstractUser
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
        verbose_name="Name",
        max_length=SKILL_NAME_MAX_LENGTH,
        unique=True,
    )

    class Meta:
        ordering = ("name",)
        verbose_name = "Skill"
        verbose_name_plural = "Skills"

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


class User(AbstractUser):
    username = None
    first_name = None
    last_name = None

    email = models.EmailField(verbose_name="Email", unique=True)
    name = models.CharField(verbose_name="Name", max_length=USER_NAME_MAX_LENGTH)
    surname = models.CharField(
        verbose_name="Surname",
        max_length=USER_SURNAME_MAX_LENGTH,
    )
    avatar = models.ImageField(verbose_name="Avatar", upload_to=avatar_upload_to)
    phone = models.CharField(
        verbose_name="Phone",
        max_length=USER_PHONE_MAX_LENGTH,
        blank=True,
        null=True,
        unique=True,
    )
    github_url = models.URLField(verbose_name="GitHub URL", blank=True)
    about = models.TextField(
        verbose_name="About",
        max_length=USER_ABOUT_MAX_LENGTH,
        blank=True,
    )
    skills = models.ManyToManyField(
        Skill,
        verbose_name="Skills",
        blank=True,
        related_name="users",
    )
    favorites = models.ManyToManyField(
        "projects.Project",
        verbose_name="Favorite projects",
        blank=True,
        related_name="interested_users",
    )
    is_active = models.BooleanField(verbose_name="Active", default=True)
    is_staff = models.BooleanField(verbose_name="Staff status", default=False)
    date_joined = models.DateTimeField(
        verbose_name="Date joined",
        default=timezone.now,
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ("name", "surname")

    class Meta:
        ordering = ("-date_joined", "-id")
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.name} {self.surname}".strip() or self.email

    def save(self, *args, **kwargs):
        if not self.avatar:
            source = self.name or self.email or "U"
            initial = source.strip()[:1].upper() or "U"
            filename = f"avatar_{uuid4()}.{AVATAR_FILE_EXTENSION}"
            self.avatar.save(filename, build_default_avatar(initial), save=False)
        super().save(*args, **kwargs)
