import json
from http import HTTPStatus

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST

from team_finder.utils import paginate

from .forms import LoginForm, ProfileForm, RegisterForm, UserPasswordChangeForm
from .models import Skill, User
from .utils import get_or_create_skill

USERS_PER_PAGE = 12
SKILL_SUGGESTIONS_LIMIT = 10
SKILL_QUERY_PARAM = "skill"
SEARCH_QUERY_PARAM = "q"
JSON_CONTENT_TYPE = "application/json"
ERROR_KEY = "error"
USER_NOT_FOUND_MESSAGE = "User not found."
SKILL_NOT_FOUND_MESSAGE = "Skill not found."
PERMISSION_DENIED_MESSAGE = "Permission denied."
SKILL_REQUIRED_MESSAGE = "skill_id or name is required"
SKILL_NOT_ATTACHED_MESSAGE = "Skill is not attached"


def json_error(message, status):
    return JsonResponse({ERROR_KEY: message}, status=status)


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("users:login")
    else:
        form = RegisterForm()
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST, request=request)
        if form.is_valid():
            login(request, form.user)
            return redirect("projects:list")
    else:
        form = LoginForm(request=request)
    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("projects:list")


def user_list(request):
    participants = (
        User.objects.filter(is_active=True)
        .prefetch_related("skills")
        .order_by("-date_joined", "-id")
    )
    active_skill = request.GET.get(SKILL_QUERY_PARAM)
    if active_skill:
        participants = participants.filter(skills__name=active_skill)
    participants = participants.distinct()
    page_obj, query_prefix = paginate(request, participants, USERS_PER_PAGE)
    context = {
        "participants": participants,
        "page_obj": page_obj,
        "query_prefix": query_prefix,
        "all_skills": Skill.objects.values_list("name", flat=True).order_by("name"),
        "active_skill": active_skill,
    }
    return render(request, "users/participants.html", context)


def user_detail(request, user_id):
    profile_user = (
        User.objects.prefetch_related("skills", "owned_projects__participants")
        .filter(pk=user_id, is_active=True)
        .first()
    )
    if profile_user is None:
        raise Http404
    return render(request, "users/user-details.html", {"user": profile_user})


@login_required(login_url="/users/login/")
def edit_profile(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("users:detail", user_id=request.user.id)
    else:
        form = ProfileForm(instance=request.user)
    return render(
        request,
        "users/edit_profile.html",
        {"form": form, "user": request.user},
    )


@login_required(login_url="/users/login/")
def change_password(request):
    if request.method == "POST":
        form = UserPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            return redirect("users:detail", user_id=request.user.id)
    else:
        form = UserPasswordChangeForm(request.user)
    return render(request, "users/change_password.html", {"form": form})


@require_GET
def skill_suggestions(request):
    query = request.GET.get(SEARCH_QUERY_PARAM, "")
    skills = Skill.objects.filter(name__istartswith=query).order_by("name")[
        :SKILL_SUGGESTIONS_LIMIT
    ]
    return JsonResponse(list(skills.values("id", "name")), safe=False)


def request_payload(request):
    if request.content_type == JSON_CONTENT_TYPE:
        try:
            return json.loads(request.body.decode() or "{}")
        except json.JSONDecodeError:
            return {}
    return request.POST


@login_required(login_url="/users/login/")
@require_POST
def add_user_skill(request, user_id):
    profile_user = User.objects.filter(pk=user_id).first()
    if profile_user is None:
        return json_error(USER_NOT_FOUND_MESSAGE, HTTPStatus.NOT_FOUND)
    if profile_user != request.user:
        return json_error(PERMISSION_DENIED_MESSAGE, HTTPStatus.FORBIDDEN)
    payload = request_payload(request)
    skill, created = get_or_create_skill(payload)
    if not skill:
        if payload.get("skill_id"):
            return json_error(SKILL_NOT_FOUND_MESSAGE, HTTPStatus.NOT_FOUND)
        return json_error(SKILL_REQUIRED_MESSAGE, HTTPStatus.BAD_REQUEST)
    before = profile_user.skills.filter(pk=skill.pk).exists()
    profile_user.skills.add(skill)
    return JsonResponse(
        {
            "id": skill.id,
            "name": skill.name,
            "skill_id": skill.id,
            "created": created,
            "added": not before,
        }
    )


@login_required(login_url="/users/login/")
@require_POST
def remove_user_skill(request, user_id, skill_id):
    profile_user = User.objects.filter(pk=user_id).first()
    if profile_user is None:
        return json_error(USER_NOT_FOUND_MESSAGE, HTTPStatus.NOT_FOUND)
    skill = Skill.objects.filter(pk=skill_id).first()
    if skill is None:
        return json_error(SKILL_NOT_FOUND_MESSAGE, HTTPStatus.NOT_FOUND)
    if profile_user != request.user:
        return json_error(PERMISSION_DENIED_MESSAGE, HTTPStatus.FORBIDDEN)
    if not profile_user.skills.filter(pk=skill.pk).exists():
        return json_error(SKILL_NOT_ATTACHED_MESSAGE, HTTPStatus.NOT_FOUND)
    profile_user.skills.remove(skill)
    return JsonResponse({"status": "ok"})
