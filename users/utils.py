import re
from urllib.parse import urlparse

from django import forms

PHONE_RE = re.compile(r"^(?:8|\+7)\d{10}$")
PHONE_LOCAL_PREFIX = "8"
PHONE_INTERNATIONAL_PREFIX = "+7"
PHONE_WITHOUT_PREFIX_START = 1
GITHUB_HOSTS = ("github.com", "www.github.com")
URL_SCHEMES = ("http", "https")
SKILL_ID_PAYLOAD_KEY = "skill_id"
SKILL_NAME_PAYLOAD_KEY = "name"


def normalize_phone(phone):
    if not phone:
        return phone
    phone = phone.strip()
    if phone.startswith(PHONE_LOCAL_PREFIX):
        return PHONE_INTERNATIONAL_PREFIX + phone[PHONE_WITHOUT_PREFIX_START:]
    return phone


def validate_github_url(value):
    if not value:
        return
    parsed = urlparse(value)
    if parsed.scheme not in URL_SCHEMES or not parsed.netloc:
        raise forms.ValidationError("Enter a valid URL.")
    if parsed.netloc.lower() not in GITHUB_HOSTS:
        raise forms.ValidationError("URL must point to GitHub.")


def get_or_create_skill(payload):
    from .models import Skill

    skill_id = payload.get(SKILL_ID_PAYLOAD_KEY)
    name = (payload.get(SKILL_NAME_PAYLOAD_KEY) or "").strip()
    if skill_id:
        return Skill.objects.filter(pk=skill_id).first(), False
    if name:
        skill, created = Skill.objects.get_or_create(name=name)
        return skill, created
    return None, False
