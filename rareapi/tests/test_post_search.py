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
def diana(db):
    return RareUser.objects.create_user(
        username='diana',
        password='pass',
        email='diana@example.com',
        is_active=True,
    )


@pytest.fixture
def bob(db):
    return RareUser.objects.create_user(
        username='bob',
        password='pass',
        email='bob@example.com',
        is_active=True,
    )


@pytest.fixture
def auth_client(api_client, diana):
    token = Token.objects.create(user=diana)
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return api_client


def make_post(user, category, title='Test Post', approved=True):
    return Post.objects.create(
        user=user,
        category=category,
        title=title,
        publication_date=datetime.date(2024, 1, 1),
        content='Some content.',
        approved=approved,
    )


class TestPostSearch:
    def test_no_params_returns_empty_list(self, auth_client):
        response = auth_client.get('/posts/search')
        assert response.status_code == 200
        assert response.json() == []

    def test_q_matches_title(self, auth_client, diana, category):
        make_post(diana, category, title='Python Tutorial')
        make_post(diana, category, title='Django Guide')
        response = auth_client.get('/posts/search?q=python')
        data = response.json()
        assert len(data) == 1
        assert data[0]['title'] == 'Python Tutorial'

    def test_q_is_case_insensitive(self, auth_client, diana, category):
        make_post(diana, category, title='Python Tutorial')
        response = auth_client.get('/posts/search?q=PYTHON')
        assert len(response.json()) == 1

    def test_author_matches_username(self, auth_client, diana, bob, category):
        make_post(diana, category, title='Post by Diana')
        make_post(bob, category, title='Post by Bob')
        response = auth_client.get('/posts/search?author=diana')
        data = response.json()
        assert len(data) == 1
        assert data[0]['title'] == 'Post by Diana'

    def test_author_is_case_insensitive(self, auth_client, diana, category):
        make_post(diana, category, title='Post by Diana')
        response = auth_client.get('/posts/search?author=DIANA')
        assert len(response.json()) == 1

    def test_author_partial_match(self, auth_client, diana, category):
        make_post(diana, category, title='Post by Diana')
        response = auth_client.get('/posts/search?author=ian')
        assert len(response.json()) == 1

    def test_combined_q_and_author(self, auth_client, diana, bob, category):
        make_post(diana, category, title='Python Tutorial')
        make_post(diana, category, title='Django Guide')
        make_post(bob, category, title='Python Basics')
        response = auth_client.get('/posts/search?q=python&author=diana')
        data = response.json()
        assert len(data) == 1
        assert data[0]['title'] == 'Python Tutorial'

    def test_unapproved_posts_excluded(self, auth_client, diana, category):
        make_post(diana, category, title='Python Tutorial', approved=False)
        response = auth_client.get('/posts/search?q=python')
        assert response.json() == []

    def test_author_no_match_returns_empty(self, auth_client, diana, category):
        make_post(diana, category, title='Python Tutorial')
        response = auth_client.get('/posts/search?author=nobody')
        assert response.json() == []
