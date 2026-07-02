import json
from http import HTTPStatus

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST

from team_finder.utils import paginate
from users.models import Skill
from users.utils import get_or_create_skill

from .forms import ProjectForm
from .models import Project

PROJECTS_PER_PAGE = 12
SKILL_SUGGESTIONS_LIMIT = 10
SKILL_QUERY_PARAM = "skill"
SEARCH_QUERY_PARAM = "q"
JSON_CONTENT_TYPE = "application/json"
ERROR_KEY = "error"
PROJECT_NOT_FOUND_MESSAGE = "Project not found."
SKILL_NOT_FOUND_MESSAGE = "Skill not found."
PERMISSION_DENIED_MESSAGE = "Permission denied."
SKILL_REQUIRED_MESSAGE = "skill_id or name is required"
SKILL_NOT_ATTACHED_MESSAGE = "Skill is not attached"


def json_error(message, status):
    return JsonResponse({ERROR_KEY: message}, status=status)


def project_list(request):
    projects = Project.objects.select_related("owner").prefetch_related(
        "participants", "skills"
    )
    active_skill = request.GET.get(SKILL_QUERY_PARAM)
    if active_skill:
        projects = projects.filter(skills__name=active_skill)
    projects = projects.distinct().order_by("-created_at", "-id")
    page_obj, query_prefix = paginate(request, projects, PROJECTS_PER_PAGE)
    context = {
        "projects": projects,
        "page_obj": page_obj,
        "query_prefix": query_prefix,
        "all_skills": Skill.objects.values_list("name", flat=True).order_by("name"),
        "active_skill": active_skill,
    }
    return render(request, "projects/project_list.html", context)


@login_required(login_url="/users/login/")
def favorite_projects(request):
    projects = request.user.favorites.select_related("owner").prefetch_related(
        "participants", "skills"
    )
    return render(request, "projects/favorite_projects.html", {"projects": projects})


def project_detail(request, project_id):
    project = (
        Project.objects.select_related("owner")
        .prefetch_related("participants", "skills")
        .filter(pk=project_id)
        .first()
    )
    if project is None:
        raise Http404
    return render(request, "projects/project-details.html", {"project": project})


@login_required(login_url="/users/login/")
def create_project(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            project.participants.add(request.user)
            return redirect("projects:detail", project_id=project.id)
    else:
        form = ProjectForm()
    return render(
        request,
        "projects/create-project.html",
        {"form": form, "is_edit": False},
    )


@login_required(login_url="/users/login/")
def edit_project(request, project_id):
    project = Project.objects.filter(pk=project_id).first()
    if project is None:
        raise Http404
    if project.owner != request.user and not request.user.is_staff:
        raise PermissionDenied
    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            project = form.save()
            return redirect("projects:detail", project_id=project.id)
    else:
        form = ProjectForm(instance=project)
    return render(
        request,
        "projects/create-project.html",
        {"form": form, "is_edit": True},
    )


@login_required(login_url="/users/login/")
@require_POST
def complete_project(request, project_id):
    project = Project.objects.filter(pk=project_id).first()
    if project is None:
        return json_error(PROJECT_NOT_FOUND_MESSAGE, HTTPStatus.NOT_FOUND)
    if project.owner != request.user and not request.user.is_staff:
        return json_error(PERMISSION_DENIED_MESSAGE, HTTPStatus.FORBIDDEN)
    if project.status == Project.STATUS_OPEN:
        project.status = Project.STATUS_CLOSED
        project.save(update_fields=("status",))
    return JsonResponse({"status": "ok", "project_status": project.status})


@login_required(login_url="/users/login/")
@require_POST
def toggle_participate(request, project_id):
    project = Project.objects.filter(pk=project_id).first()
    if project is None:
        return json_error(PROJECT_NOT_FOUND_MESSAGE, HTTPStatus.NOT_FOUND)
    if project.owner == request.user:
        return JsonResponse({"status": "ok", "participant": True})
    participant = not project.participants.filter(pk=request.user.pk).exists()
    if participant:
        project.participants.add(request.user)
    else:
        project.participants.remove(request.user)
    return JsonResponse({"status": "ok", "participant": participant})


@login_required(login_url="/users/login/")
@require_POST
def toggle_favorite(request, project_id):
    project = Project.objects.filter(pk=project_id).first()
    if project is None:
        return json_error(PROJECT_NOT_FOUND_MESSAGE, HTTPStatus.NOT_FOUND)
    favorited = not request.user.favorites.filter(pk=project.pk).exists()
    if favorited:
        request.user.favorites.add(project)
    else:
        request.user.favorites.remove(project)
    return JsonResponse({"status": "ok", "favorited": favorited})


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
def add_project_skill(request, project_id):
    project = Project.objects.filter(pk=project_id).first()
    if project is None:
        return json_error(PROJECT_NOT_FOUND_MESSAGE, HTTPStatus.NOT_FOUND)
    if project.owner != request.user and not request.user.is_staff:
        return json_error(PERMISSION_DENIED_MESSAGE, HTTPStatus.FORBIDDEN)
    payload = request_payload(request)
    skill, created = get_or_create_skill(payload)
    if not skill:
        if payload.get("skill_id"):
            return json_error(SKILL_NOT_FOUND_MESSAGE, HTTPStatus.NOT_FOUND)
        return json_error(SKILL_REQUIRED_MESSAGE, HTTPStatus.BAD_REQUEST)
    before = project.skills.filter(pk=skill.pk).exists()
    project.skills.add(skill)
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
def remove_project_skill(request, project_id, skill_id):
    project = Project.objects.filter(pk=project_id).first()
    if project is None:
        return json_error(PROJECT_NOT_FOUND_MESSAGE, HTTPStatus.NOT_FOUND)
    skill = Skill.objects.filter(pk=skill_id).first()
    if skill is None:
        return json_error(SKILL_NOT_FOUND_MESSAGE, HTTPStatus.NOT_FOUND)
    if project.owner != request.user and not request.user.is_staff:
        return json_error(PERMISSION_DENIED_MESSAGE, HTTPStatus.FORBIDDEN)
    if not project.skills.filter(pk=skill.pk).exists():
        return json_error(SKILL_NOT_ATTACHED_MESSAGE, HTTPStatus.NOT_FOUND)
    project.skills.remove(skill)
    return JsonResponse({"status": "ok"})
