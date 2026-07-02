from django.core.management.base import BaseCommand

from projects.models import Project
from users.models import Skill, User

DEMO_PASSWORD = "password"
DEMO_USERS = (
    {
        "email": "maria@yandex.ru",
        "name": "Maria",
        "surname": "Sokolova",
        "phone": "+79000000001",
        "github_url": "https://github.com/maria",
        "about": "Backend developer looking for Django projects.",
        "skills": ("Django", "PostgreSQL", "Docker"),
    },
    {
        "email": "ivan@example.com",
        "name": "Ivan",
        "surname": "Petrov",
        "phone": "+79000000002",
        "github_url": "https://github.com/ivan",
        "about": "Frontend-focused teammate with product sense.",
        "skills": ("JavaScript", "HTML", "CSS"),
    },
    {
        "email": "anna@example.com",
        "name": "Anna",
        "surname": "Smirnova",
        "phone": "+79000000003",
        "github_url": "https://github.com/anna",
        "about": "Designer and analyst for small product teams.",
        "skills": ("UX", "Research", "Figma"),
    },
)
DEMO_PROJECTS = (
    {
        "owner": "maria@yandex.ru",
        "name": "Mentor Board",
        "description": "A service for matching students with mentors.",
        "github_url": "https://github.com/example/mentor-board",
        "skills": ("Django", "PostgreSQL"),
    },
    {
        "owner": "ivan@example.com",
        "name": "Study Planner",
        "description": "A lightweight planner for course teams.",
        "github_url": "https://github.com/example/study-planner",
        "skills": ("JavaScript", "CSS"),
    },
    {
        "owner": "anna@example.com",
        "name": "Interview Notes",
        "description": "A shared note space for product interviews.",
        "github_url": "https://github.com/example/interview-notes",
        "skills": ("UX", "Research"),
    },
)


class Command(BaseCommand):
    help = "Create demo users, skills, and projects."

    def handle(self, *args, **options):
        users = {}
        for user_data in DEMO_USERS:
            skill_names = user_data["skills"]
            user_defaults = {
                key: value for key, value in user_data.items() if key != "skills"
            }
            user, created = User.objects.get_or_create(
                email=user_data["email"],
                defaults=user_defaults,
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()
            else:
                for field, value in user_defaults.items():
                    setattr(user, field, value)
                user.set_password(DEMO_PASSWORD)
                user.save()
            for skill_name in skill_names:
                skill, _ = Skill.objects.get_or_create(name=skill_name)
                user.skills.add(skill)
            users[user.email] = user

        for project_data in DEMO_PROJECTS:
            owner = users[project_data["owner"]]
            project, _ = Project.objects.get_or_create(
                owner=owner,
                name=project_data["name"],
                defaults={
                    "description": project_data["description"],
                    "github_url": project_data["github_url"],
                },
            )
            project.participants.add(owner)
            for skill_name in project_data["skills"]:
                skill, _ = Skill.objects.get_or_create(name=skill_name)
                project.skills.add(skill)

        self.stdout.write(self.style.SUCCESS("Demo data is ready."))
