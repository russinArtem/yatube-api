from django.shortcuts import get_object_or_404
from rest_framework import filters, permissions, serializers, viewsets
from rest_framework.pagination import LimitOffsetPagination

from .serializers import (
    CommentSerializer, FollowSerializer, GroupSerializer, PostSerializer)
from posts.models import Follow, Group, Post, User


class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, instance):
        return (
            request.method in permissions.SAFE_METHODS
            or instance.author == request.user
        )


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsAuthorOrReadOnly
    ]
    pagination_class = LimitOffsetPagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsAuthorOrReadOnly
    ]

    def get_post(self):
        return get_object_or_404(Post, pk=self.kwargs['post_id'])

    def get_queryset(self):
        return self.get_post().comments.all()

    def perform_create(self, serializer):
        serializer.save(post=self.get_post(), author=self.request.user)


class FollowViewSet(viewsets.ModelViewSet):
    serializer_class = FollowSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['following__username']

    def get_queryset(self):
        return Follow.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        user = self.request.user
        following_username = self.request.data.get('following')
        if user.username == following_username:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя'
            )
        following_user = User.objects.get(username=following_username)
        if Follow.objects.filter(user=user, following=following_user).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого автора'
            )
        serializer.save(user=user, following=following_user)
