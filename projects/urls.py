from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("list", views.project_list, name="list"),
    path("list/", views.project_list),
    path("favorites/", views.favorite_projects, name="favorites"),
    path("create-project", views.create_project, name="create"),
    path("create-project/", views.create_project),
    path("skills/", views.skill_suggestions, name="skills"),
    path("<int:project_id>", views.project_detail, name="detail"),
    path("<int:project_id>/", views.project_detail),
    path("<int:project_id>/edit", views.edit_project, name="edit"),
    path("<int:project_id>/edit/", views.edit_project),
    path("<int:project_id>/complete/", views.complete_project, name="complete"),
    path(
        "<int:project_id>/toggle-participate/",
        views.toggle_participate,
        name="toggle_participate",
    ),
    path(
        "<int:project_id>/toggle-favorite/",
        views.toggle_favorite,
        name="toggle_favorite",
    ),
    path("<int:project_id>/skills/add/", views.add_project_skill, name="add_skill"),
    path(
        "<int:project_id>/skills/<int:skill_id>/remove/",
        views.remove_project_skill,
        name="remove_skill",
    ),
]
