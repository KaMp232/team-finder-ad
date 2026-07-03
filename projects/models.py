from django.conf import settings
from django.db import models

from users.models import Skill

PROJECT_NAME_MAX_LENGTH = 200
PROJECT_STATUS_MAX_LENGTH = 6


class Project(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"

    name = models.CharField(verbose_name="Name", max_length=PROJECT_NAME_MAX_LENGTH)
    description = models.TextField(verbose_name="Description", blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Owner",
        on_delete=models.CASCADE,
        related_name="owned_projects",
    )
    created_at = models.DateTimeField(
        verbose_name="Created at",
        auto_now_add=True,
        db_index=True,
    )
    github_url = models.URLField(verbose_name="GitHub URL", blank=True)
    status = models.CharField(
        verbose_name="Status",
        max_length=PROJECT_STATUS_MAX_LENGTH,
        choices=Status.choices,
        default=Status.OPEN,
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name="Participants",
        blank=True,
        related_name="participated_projects",
    )
    skills = models.ManyToManyField(
        Skill,
        verbose_name="Skills",
        blank=True,
        related_name="projects",
    )

    class Meta:
        ordering = ("-created_at", "-id")
        verbose_name = "Project"
        verbose_name_plural = "Projects"

    def __str__(self):
        return self.name
