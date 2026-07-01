import datetime
import pytest
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from rareapi.models import Category, Comment, Post, PostReaction, Reaction, RareUser


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
def category(db):
    return Category.objects.create(label='General')


@pytest.fixture
def auth_client(db, user):
    client = APIClient()
    token = Token.objects.create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return client


@pytest.fixture
def post(user, category):
    return Post.objects.create(
        user=user,
        category=category,
        title='Hello World',
        publication_date=datetime.date(2024, 1, 1),
        content='A' * 200,
        approved=True,
    )


@pytest.fixture
def reaction_type(db):
    return Reaction.objects.create(label='like', image_url='')


class TestPostListFields:
    def test_excerpt_present_and_truncated(self, auth_client, post):
        response = auth_client.get('/posts')
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert 'excerpt' in data[0]
        assert len(data[0]['excerpt']) <= 151  # 150 chars + ellipsis char

    def test_excerpt_not_truncated_when_short(self, auth_client, user, category):
        Post.objects.create(
            user=user, category=category,
            title='Short', publication_date=datetime.date(2024, 1, 1),
            content='Brief content.', approved=True,
        )
        response = auth_client.get('/posts')
        post_data = next(p for p in response.json() if p['title'] == 'Short')
        assert post_data['excerpt'] == 'Brief content.'

    def test_comment_count_is_zero_with_no_comments(self, auth_client, post):
        response = auth_client.get('/posts')
        assert response.json()[0]['comment_count'] == 0

    def test_comment_count_reflects_comments(self, auth_client, post, user):
        Comment.objects.create(post=post, author=user, content='First', subject='Hi')
        Comment.objects.create(post=post, author=user, content='Second', subject='Hi')
        response = auth_client.get('/posts')
        assert response.json()[0]['comment_count'] == 2

    def test_reaction_count_is_zero_with_no_reactions(self, auth_client, post):
        response = auth_client.get('/posts')
        assert response.json()[0]['reaction_count'] == 0

    def test_reaction_count_reflects_reactions(self, auth_client, post, user, reaction_type):
        PostReaction.objects.create(post=post, user=user, reaction=reaction_type)
        response = auth_client.get('/posts')
        assert response.json()[0]['reaction_count'] == 1

    def test_user_includes_first_and_last_name(self, auth_client, post):
        response = auth_client.get('/posts')
        user_data = response.json()[0]['user']
        assert user_data['first_name'] == 'Jane'
        assert user_data['last_name'] == 'Doe'
