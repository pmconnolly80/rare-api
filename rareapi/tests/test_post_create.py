import pytest
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from rareapi.models import RareUser, Category


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def category(db):
    return Category.objects.create(label='Tech')


@pytest.fixture
def regular_user(db):
    return RareUser.objects.create_user(
        username='author', password='pass', email='author@example.com', is_active=True,
    )


@pytest.fixture
def staff_user(db):
    return RareUser.objects.create_user(
        username='admin', password='pass', email='admin@example.com',
        is_active=True, is_staff=True,
    )


def auth_client_for(user):
    client = APIClient()
    token = Token.objects.create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return client


def post_payload(category):
    return {'title': 'Test Post', 'category_id': category.id, 'content': 'Some content.'}


class TestPostCreate:
    def test_non_staff_post_is_unapproved(self, regular_user, category):
        client = auth_client_for(regular_user)
        response = client.post('/posts', post_payload(category), format='json')
        assert response.status_code == 201
        assert response.json()['approved'] is False

    def test_staff_post_is_auto_approved(self, staff_user, category):
        client = auth_client_for(staff_user)
        response = client.post('/posts', post_payload(category), format='json')
        assert response.status_code == 201
        assert response.json()['approved'] is True
