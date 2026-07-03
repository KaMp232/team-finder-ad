from http import HTTPStatus

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST

from team_finder.constants import (
    DEFAULT_PAGE_SIZE,
    PERMISSION_DENIED_MESSAGE,
    SEARCH_QUERY_PARAM,
    SKILL_NOT_ATTACHED_MESSAGE,
    SKILL_NOT_FOUND_MESSAGE,
    SKILL_QUERY_PARAM,
    SKILL_REQUIRED_MESSAGE,
    SKILL_SUGGESTIONS_LIMIT,
)
from team_finder.utils import json_error, paginate, request_payload

from .forms import LoginForm, ProfileForm, RegisterForm, UserPasswordChangeForm
from .models import Skill, User
from .utils import get_or_create_skill

USER_NOT_FOUND_MESSAGE = "User not found."


def register(request):
    form = RegisterForm(request.POST or None)
    if request.method != "POST":
        return render(request, "users/register.html", {"form": form})

    if not form.is_valid():
        return render(request, "users/register.html", {"form": form})

    form.save()
    return redirect("users:login")


def login_view(request):
    form = LoginForm(request.POST or None, request=request)
    if request.method != "POST":
        return render(request, "users/login.html", {"form": form})

    if not form.is_valid():
        return render(request, "users/login.html", {"form": form})

    login(request, form.user)
    return redirect("projects:list")


def logout_view(request):
    logout(request)
    return redirect("projects:list")


def user_list(request):
    participants = User.objects.filter(is_active=True).prefetch_related("skills")
    active_skill = request.GET.get(SKILL_QUERY_PARAM)
    if active_skill:
        participants = participants.filter(skills__name=active_skill)
    participants = participants.distinct()
    page_obj, query_prefix = paginate(request, participants, DEFAULT_PAGE_SIZE)
    context = {
        "participants": participants,
        "page_obj": page_obj,
        "query_prefix": query_prefix,
        "all_skills": Skill.objects.values_list("name", flat=True),
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
    form = ProfileForm(
        request.POST or None,
        request.FILES or None,
        instance=request.user,
    )
    if request.method != "POST":
        return render(
            request,
            "users/edit_profile.html",
            {"form": form, "user": request.user},
        )

    if not form.is_valid():
        return render(
            request,
            "users/edit_profile.html",
            {"form": form, "user": request.user},
        )

    form.save()
    return redirect("users:detail", user_id=request.user.id)


@login_required(login_url="/users/login/")
def change_password(request):
    form = UserPasswordChangeForm(request.user, request.POST or None)
    if request.method != "POST":
        return render(request, "users/change_password.html", {"form": form})

    if not form.is_valid():
        return render(request, "users/change_password.html", {"form": form})

    form.save()
    return redirect("users:detail", user_id=request.user.id)


@require_GET
def skill_suggestions(request):
    query = request.GET.get(SEARCH_QUERY_PARAM, "")
    skills = Skill.objects.filter(name__istartswith=query)[:SKILL_SUGGESTIONS_LIMIT]
    return JsonResponse(list(skills.values("id", "name")), safe=False)


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
