import pytest
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from rareapi.models import RareUser


def auth_client_for(user):
    client = APIClient()
    token = Token.objects.create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return client


@pytest.fixture
def owner(db):
    return RareUser.objects.create_user(
        username='owner', password='pass', email='owner@example.com',
        first_name='Alice', last_name='Smith', bio='Old bio', is_active=True,
    )


@pytest.fixture
def other_user(db):
    return RareUser.objects.create_user(
        username='other', password='pass', email='other@example.com', is_active=True,
    )


class TestProfileUpdate:
    def test_owner_can_update_profile(self, owner):
        client = auth_client_for(owner)
        response = client.put(
            f'/profiles/{owner.id}',
            {'first_name': 'Bob', 'last_name': 'Jones', 'bio': 'New bio'},
            format='json',
        )
        assert response.status_code == 200
        data = response.json()
        assert data['first_name'] == 'Bob'
        assert data['last_name'] == 'Jones'
        assert data['bio'] == 'New bio'
        owner.refresh_from_db()
        assert owner.first_name == 'Bob'

    def test_owner_can_do_partial_update(self, owner):
        client = auth_client_for(owner)
        response = client.put(
            f'/profiles/{owner.id}',
            {'bio': 'Just the bio'},
            format='json',
        )
        assert response.status_code == 200
        assert response.json()['bio'] == 'Just the bio'
        owner.refresh_from_db()
        assert owner.first_name == 'Alice'

    def test_non_owner_cannot_update(self, owner, other_user):
        client = auth_client_for(other_user)
        response = client.put(
            f'/profiles/{owner.id}',
            {'bio': 'Hacked'},
            format='json',
        )
        assert response.status_code == 403

    def test_unauthenticated_cannot_update(self, owner):
        client = APIClient()
        response = client.put(
            f'/profiles/{owner.id}',
            {'bio': 'Hacked'},
            format='json',
        )
        assert response.status_code == 401
