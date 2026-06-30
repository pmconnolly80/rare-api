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
def other_user(db):
    return RareUser.objects.create_user(
        username='other', password='pass', email='other@example.com', is_active=True,
    )


@pytest.fixture
def admin_user(db):
    return RareUser.objects.create_user(
        username='admin', password='pass', email='admin@example.com',
        is_active=True, is_staff=True,
    )


def auth_client_for(user):
    client = APIClient()
    token = Token.objects.create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return client


def make_post(user, category, approved=True):
    return Post.objects.create(
        user=user,
        category=category,
        title='Test Post',
        publication_date=datetime.date(2024, 1, 1),
        content='Content.',
        approved=approved,
    )


class TestPostDetailAccess:
    def test_approved_post_visible_to_any_user(self, author, other_user, category):
        post = make_post(author, category, approved=True)
        client = auth_client_for(other_user)
        response = client.get(f'/posts/{post.id}')
        assert response.status_code == 200

    def test_unapproved_post_visible_to_author(self, author, category):
        post = make_post(author, category, approved=False)
        client = auth_client_for(author)
        response = client.get(f'/posts/{post.id}')
        assert response.status_code == 200

    def test_unapproved_post_visible_to_admin(self, author, admin_user, category):
        post = make_post(author, category, approved=False)
        client = auth_client_for(admin_user)
        response = client.get(f'/posts/{post.id}')
        assert response.status_code == 200

    def test_unapproved_post_hidden_from_other_user(self, author, other_user, category):
        post = make_post(author, category, approved=False)
        client = auth_client_for(other_user)
        response = client.get(f'/posts/{post.id}')
        assert response.status_code == 404
