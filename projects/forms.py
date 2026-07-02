from django import forms

from users.utils import validate_github_url

from .models import Project

PROJECT_DESCRIPTION_ROWS = 6
GITHUB_WIDGET_ATTRS = {"placeholder": "https://github.com/team/project"}


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ("name", "description", "github_url", "status")
        widgets = {
            "description": forms.Textarea(attrs={"rows": PROJECT_DESCRIPTION_ROWS}),
            "github_url": forms.URLInput(attrs=GITHUB_WIDGET_ATTRS),
        }
        labels = {
            "name": "Name",
            "description": "Description",
            "github_url": "GitHub URL",
            "status": "Status",
        }

    def clean_github_url(self):
        github_url = self.cleaned_data.get("github_url")
        validate_github_url(github_url)
        return github_url
