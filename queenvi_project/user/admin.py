from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import Count

from core.constants import AdminConstants
from post.models import Comment, Post
from youtube_suggestion.models import Video


User = get_user_model()


class PostInline(admin.TabularInline):
    model = Post
    extra = AdminConstants.NO_EXTRA


class VideoInline(PostInline):
    model = Video


class CommentInline(PostInline):
    model = Comment


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    inlines = [PostInline, VideoInline, CommentInline]
    list_display = (
        'username', 'role', 'is_banned', 'posts_count', 'videos_count',
        'comments_count', 'created_at', 'updated_at',
    )
    list_filter = ('role', 'is_banned', 'created_at',)
    search_fields = ('username',)
    ordering = ('-created_at',)
    readonly_fields = ('posts_count', 'videos_count', 'comments_count')
    fieldsets = (
        ('Основное', {'fields': ('username',)}),
        ('Активность', {
            'fields': ('posts_count', 'videos_count', 'comments_count')
        }),
        ('Модерация', {'fields': ('role', 'is_banned')}),
        ('Аватарки', {'fields': ('twitch_avatar', 'custom_avatar',)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            posts_count=Count('posts', distinct=True),
            videos_count=Count('videos', distinct=True),
            comments_count=Count('commented_posts', distinct=True),
        )

    @admin.display(description='Посты', ordering='posts_count')
    def posts_count(self, obj):
        return obj.posts_count

    @admin.display(description='Видео', ordering='videos_count')
    def videos_count(self, obj):
        return obj.videos_count

    @admin.display(description='Коммы', ordering='comments_count')
    def comments_count(self, obj):
        return obj.comments_count
