import datetime
import pytest
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from rareapi.models import RareUser, Post, Category


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def category(db):
    return Category.objects.create(label='Tech')


@pytest.fixture
def author(db):
    return RareUser.objects.create_user(
        username='author', password='pass', email='author@example.com', is_active=True,
    )


@pytest.fixture
def viewer(db):
    return RareUser.objects.create_user(
        username='viewer', password='pass', email='viewer@example.com', is_active=True,
    )


@pytest.fixture
def auth_client(api_client, viewer):
    token = Token.objects.create(user=viewer)
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return api_client


def make_post(user, category, publication_date, approved=True):
    return Post.objects.create(
        user=user,
        category=category,
        title='Test Post',
        publication_date=publication_date,
        content='Content.',
        approved=approved,
    )


class TestUserPostList:
    def test_published_approved_post_is_visible(self, auth_client, author, category):
        make_post(author, category, datetime.date(2024, 1, 1))
        response = auth_client.get(f'/profiles/{author.pk}/posts')
        assert len(response.json()) == 1

    def test_future_approved_post_is_hidden(self, auth_client, author, category):
        make_post(author, category, datetime.date(2099, 1, 1))
        response = auth_client.get(f'/profiles/{author.pk}/posts')
        assert response.json() == []

    def test_unapproved_post_is_hidden(self, auth_client, author, category):
        make_post(author, category, datetime.date(2024, 1, 1), approved=False)
        response = auth_client.get(f'/profiles/{author.pk}/posts')
        assert response.json() == []
