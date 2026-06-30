import datetime
import pytest
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from rareapi.models import RareUser, Post, Category


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return RareUser.objects.create_user(
        username='author',
        password='pass',
        first_name='Jane',
        last_name='Doe',
        email='jane@example.com',
        is_active=True,
    )


@pytest.fixture
def other_user(db):
    return RareUser.objects.create_user(
        username='other',
        password='pass',
        is_active=True,
    )


@pytest.fixture
def category(db):
    return Category.objects.create(label='General')


@pytest.fixture
def auth_client(api_client, user):
    token = Token.objects.create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return api_client


def make_post(user, category, approved=True):
    return Post.objects.create(
        user=user,
        category=category,
        title='Test Post',
        publication_date=datetime.date(2024, 1, 1),
        content='Some content.',
        approved=approved,
    )


class TestProfilePostCount:
    def test_field_is_present_in_response(self, auth_client, user):
        response = auth_client.get(f'/profiles/{user.pk}')
        assert response.status_code == 200
        assert 'post_count' in response.json()

    def test_zero_when_user_has_no_posts(self, auth_client, user):
        response = auth_client.get(f'/profiles/{user.pk}')
        assert response.json()['post_count'] == 0

    def test_zero_when_all_posts_are_unapproved(self, auth_client, user, category):
        make_post(user, category, approved=False)
        make_post(user, category, approved=False)
        response = auth_client.get(f'/profiles/{user.pk}')
        assert response.json()['post_count'] == 0

    def test_counts_only_approved_posts(self, auth_client, user, category):
        make_post(user, category, approved=True)
        make_post(user, category, approved=True)
        make_post(user, category, approved=False)
        response = auth_client.get(f'/profiles/{user.pk}')
        assert response.json()['post_count'] == 2

    def test_counts_all_approved_posts(self, auth_client, user, category):
        for _ in range(5):
            make_post(user, category, approved=True)
        response = auth_client.get(f'/profiles/{user.pk}')
        assert response.json()['post_count'] == 5

    def test_excludes_other_users_approved_posts(self, auth_client, user, other_user, category):
        make_post(other_user, category, approved=True)
        make_post(other_user, category, approved=True)
        make_post(user, category, approved=True)
        response = auth_client.get(f'/profiles/{user.pk}')
        assert response.json()['post_count'] == 1
