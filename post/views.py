from django.shortcuts import render

import re

from rest_framework import viewsets, mixins
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action

from .models import *
from .serializers import *
from .permissions import *

from django.shortcuts import get_object_or_404

# Create your views here.

#======================================================================
class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    
    def get_serializer_class(self):
        if self.action == "list":
            return PostListSerializer
        return PostSerializer
    
    def get_permissions(self):
        if self.action in ["update", "destroy", "partial_update"]:
            return [IsOwnerOrReadOnly()]
        return []

    
    def create(self, request):
        serializer = self.get_serializer(data = request.data)
        serializer.is_valid(raise_exception = True)
        self.perform_create(serializer)
        
        post = serializer.instance
        self.handle_tags(post)
        
        return Response(serializer.data)
    
    def perform_update(self, serializer):
        post = serializer.save()
        post.tags.clear()
        self.handle_tags(post)
        
    def handle_tags(self, post):
        words = re.split(r'[\s,]+', post.content.strip())
        tag_list = []
        
        for w in words:
            if len(w) > 0:
                if w[0] == '#':
                    tag_list.append(w[1:])
        for t in tag_list:
            tag, _ = Tag.objects.get_or_create(name=t)
            post.tags.add(tag)
        post.save()

    @action(methods = ["GET"], detail = False)
    def recommend(self, request):
        ran_post = self.get_queryset().order_by("?").first()
        ran_post_serializer = PostListSerializer(ran_post)
        return Response(ran_post_serializer.data)

    @action(methods=["GET"], detail=True)
    def test(self, request, pk=None):
        test_post = self.get_object()
        test_post.click_num += 1
        test_post.save(update_fields = ["click_num"])
        return Response()
    
    #좋아요 (유저별 한 번만 누르기 가능)
    ## detail = True : 하나의 객체에 대해 동작
    @action(methods=["POST"], detail=True, permission_classes =[IsAuthenticated])
    def like(self, request, pk = None):
        like_post = self.get_object()
        user = request.user
        
        if user in like_post.likes.all():
            like_post.likes.remove(user)
            like_post.like_count -= 1
            like_post.save(update_fields = ["like_count"])
            return Response({"message": "좋아요 취소"})
        else:
            like_post.likes.add(user)
            like_post.like_count += 1
            like_post.save(update_fields = ["like_count"])
            return Response({"message": "좋아요 추가"})
    
    #좋아요 상위 3개 post
    ## detail = False : 여러 객체에 대해 동작
    @action(methods=["GET"], detail = False)
    def topLike(self, request):
        topLike_posts = self.get_queryset().order_by('-like_count')[:3]
        topLike_posts_serializer = PostListSerializer(topLike_posts, many=True)
        return Response(topLike_posts_serializer.data)


#======================================================================

class CommentViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    
    def get_permissions(self):
        if self.action in ["update", "destroy", "partial_update"]:
            return [IsOwnerOrReadOnly()]
        return []
    
    
    
class PostCommentViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin):
    #queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        post = self.kwargs.get("post_id")
        queryset = Comment.objects.filter(post_id = post)
        return queryset

    def create(self, request, post_id = None):
        post = get_object_or_404(Post, id=post_id)
        serializer = self.get_serializer(data = request.data)
        serializer.is_valid(raise_exception = True)
        serializer.save(post=post)
        return Response(serializer.data)
    
#======================================================================   
    
class TagViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = "name"
    lookup_url_kwarg = "tag_name"
    
    def retrieve(self, request, *args, **kwargs):
        tag_name = kwargs.get("tag_name")
        tags = get_object_or_404(Tag, name = tag_name)
        posts = Post.objects.filter(tags = tags)
        serializer = PostSerializer(posts, many = True)
        return Response(serializer.data)