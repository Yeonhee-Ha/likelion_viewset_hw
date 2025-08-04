from django.db import models
from django.contrib.auth.models import User

class Tag(models.Model):
    id = models.AutoField(primary_key= True)
    name = models.CharField(max_length=50)


def image_upload_path(instance, filename):
    return f'{instance.pk}/{filename}'

class Post(models.Model):
    id = models.AutoField(primary_key=True)
    writer = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now = True)
    tags = models.ManyToManyField(Tag, blank=True)
    image = models.ImageField(upload_to=image_upload_path, blank=True, null = True)
    click_num = models.PositiveSmallIntegerField(default=0)
    like_count = models.PositiveSmallIntegerField(default =0)
    likes = models.ManyToManyField(User, related_name="liked_posts", blank = True)
    
    
class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    post = models.ForeignKey(Post, blank=False, null=False, on_delete=models.CASCADE, related_name='comments')
    writer = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    