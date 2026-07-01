from rest_framework import serializers
from rareapi.models import Post
from .user_serializers import UserSummarySerializer
from .category_serializers import CategorySerializer
from .tag_serializers import TagSerializer


class PostDetailSerializer(serializers.ModelSerializer):
    """Full post representation with tags, used for detail and create/update responses."""
    user = UserSummarySerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'content', 'publication_date',
            'image_url', 'approved', 'user', 'category', 'tags',
        ]

    def get_tags(self, obj):
        return TagSerializer(
            [pt.tag for pt in obj.post_tags.select_related('tag').all()],
            many=True,
        ).data


class PostListSerializer(serializers.ModelSerializer):
    """Slim post representation for list endpoints."""
    user = UserSummarySerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    excerpt = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    reaction_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'excerpt', 'publication_date', 'approved',
            'user', 'category', 'comment_count', 'reaction_count',
        ]

    def get_excerpt(self, obj):
        if len(obj.content) > 150:
            return obj.content[:150] + '…'
        return obj.content

    def get_comment_count(self, obj):
        return obj.comments.count()

    def get_reaction_count(self, obj):
        return obj.post_reactions.count()
