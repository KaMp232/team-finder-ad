from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse

from users.models import Skill, User

from .models import Project

DEFAULT_PASSWORD = "password"
OWNER_EMAIL = "owner@example.com"
OWNER_NAME = "Owner"
OWNER_SURNAME = "User"
OWNER_PHONE = "+79000000101"
MEMBER_EMAIL = "member@example.com"
MEMBER_NAME = "Member"
MEMBER_SURNAME = "User"
MEMBER_PHONE = "+79000000102"
NEW_USER_EMAIL = "new@example.com"
NEW_USER_NAME = "New"
NEW_USER_SURNAME = "User"
PROJECT_NAME = "Demo project"
PROJECT_DESCRIPTION = "Demo description"
PROJECT_GITHUB_URL = "https://github.com/example/demo"
SKILL_NAME = "Django"
PARTICIPANT_RESPONSE_KEY = "participant"
SKILL_FILTER_PARAM = "skill"
EMAIL_FIELD = "email"
PASSWORD_FIELD = "password"
NAME_FIELD = "name"
SURNAME_FIELD = "surname"
PROJECT_LIST_URL_NAME = "projects:list"
PROJECT_TOGGLE_PARTICIPATE_URL_NAME = "projects:toggle_participate"
USERS_REGISTER_URL_NAME = "users:register"
USERS_LOGIN_URL_NAME = "users:login"
USERS_LIST_URL_NAME = "users:list"


class TeamFinderSmokeTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email=OWNER_EMAIL,
            password=DEFAULT_PASSWORD,
            name=OWNER_NAME,
            surname=OWNER_SURNAME,
            phone=OWNER_PHONE,
        )
        self.member = User.objects.create_user(
            email=MEMBER_EMAIL,
            password=DEFAULT_PASSWORD,
            name=MEMBER_NAME,
            surname=MEMBER_SURNAME,
            phone=MEMBER_PHONE,
        )
        self.project = Project.objects.create(
            name=PROJECT_NAME,
            description=PROJECT_DESCRIPTION,
            owner=self.owner,
            github_url=PROJECT_GITHUB_URL,
        )
        self.project.participants.add(self.owner)

    def test_project_list_is_available(self):
        response = self.client.get(reverse(PROJECT_LIST_URL_NAME))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, PROJECT_NAME)

    def test_register_redirects_to_login(self):
        response = self.client.post(
            reverse(USERS_REGISTER_URL_NAME),
            {
                EMAIL_FIELD: NEW_USER_EMAIL,
                PASSWORD_FIELD: DEFAULT_PASSWORD,
                NAME_FIELD: NEW_USER_NAME,
                SURNAME_FIELD: NEW_USER_SURNAME,
            },
        )
        self.assertRedirects(response, reverse(USERS_LOGIN_URL_NAME))
        self.assertTrue(User.objects.filter(email=NEW_USER_EMAIL).exists())

    def test_login_by_email(self):
        response = self.client.post(
            reverse(USERS_LOGIN_URL_NAME),
            {EMAIL_FIELD: MEMBER_EMAIL, PASSWORD_FIELD: DEFAULT_PASSWORD},
        )
        self.assertRedirects(response, reverse(PROJECT_LIST_URL_NAME))

    def test_toggle_participation(self):
        self.client.force_login(self.member)
        response = self.client.post(
            reverse(PROJECT_TOGGLE_PARTICIPATE_URL_NAME, args=[self.project.id])
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response.json()[PARTICIPANT_RESPONSE_KEY])
        self.assertTrue(self.project.participants.filter(pk=self.member.pk).exists())

    def test_users_skill_filter(self):
        skill = Skill.objects.create(name=SKILL_NAME)
        self.member.skills.add(skill)
        response = self.client.get(
            reverse(USERS_LIST_URL_NAME), {SKILL_FILTER_PARAM: SKILL_NAME}
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, MEMBER_NAME)
        self.assertNotContains(response, OWNER_NAME)
