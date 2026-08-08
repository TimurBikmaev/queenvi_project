from django.contrib import admin
from django.db.models import Count

from core.constants import AdminConstants
from post.models import Comment, Media, Post, Report


class AuthorPostMixin(admin.ModelAdmin):
    @admin.display(description='Автор')
    def author(self, obj):
        return obj.user.username

    @admin.display(description='ID поста')
    def post_public_id(self, obj):
        return obj.post.public_id


class MediaInline(admin.TabularInline):
    model = Media
    extra = AdminConstants.NO_EXTRA


class CommentInline(MediaInline):
    model = Comment


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    inlines = [MediaInline, CommentInline]
    list_display = (
        'public_id', 'author', 'name', 'is_for_stream', 'is_banned',
        'likes_count', 'comments_count', 'created_at', 'updated_at',
    )
    list_filter = ('is_for_stream', 'is_banned', 'created_at',)
    search_fields = ('name', 'user__username', 'public_id')
    ordering = ('-created_at',)
    readonly_fields = ('likes_count', 'comments_count')
    fieldsets = (
        ('Основное', {'fields': ('name', 'user', 'is_for_stream')}),
        ('Дополнительноe', {
            'fields': ('description', 'likes_count', 'comments_count')
        }),
        ('Модерация', {'fields': ('is_banned',)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            likes_count=Count('likes', distinct=True),
            comments_count=Count('comments', distinct=True)
        )

    @admin.display(description='Лайки', ordering='likes_count')
    def likes_count(self, obj):
        return obj.likes_count

    @admin.display(description='Коммы', ordering='comments_count')
    def comments_count(self, obj):
        return obj.comments_count

    @admin.display(description='Автор')
    def author(self, obj):
        return obj.user.username


@admin.register(Comment)
class CommentAdmin(AuthorPostMixin):
    list_display = (
        'public_id', 'author', 'post_public_id', 'text',
        'created_at', 'updated_at',
    )
    list_filter = ('created_at',)
    search_fields = ('user__username', 'public_id')
    ordering = ('-created_at',)
    fieldsets = (
        ('Сообщение', {'fields': ('text', 'user',)}),
        ('Пост', {'fields': ('post',)}),
    )


@admin.register(Report)
class ReportAdmin(AuthorPostMixin):
    list_display = (
        'public_id', 'author', 'post_public_id', 'status', 'reason',
        'moder_user', 'created_at', 'updated_at',
    )
    list_filter = ('status', 'reason', 'created_at',)
    search_fields = (
        'public_id', 'user__username', 'post__public_id', 'moder__username'
    )
    ordering = ('-created_at',)
    fieldsets = (
        ('Причина', {'fields': ('reason', 'other',)}),
        ('От кого и на что', {'fields': ('user', 'post')}),
        ('Модерация', {'fields': ('status', 'moder')}),
    )

    @admin.display(description='Модер')
    def moder_user(self, obj):
        return obj.moder.username if obj.moder else '—'
