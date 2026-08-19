from django.contrib import admin
from django.db.models import Count

from youtube_suggestion.models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = (
        'public_id', 'author', 'category', 'votings_count', 'is_banned',
        'created_at', 'updated_at',
    )
    list_filter = ('category', 'is_banned', 'created_at',)
    search_fields = ('public_id', 'user__username',)
    readonly_fields = ('votings_count',)
    fieldsets = (
        ('Основное', {'fields': ('youtube_id', 'user', 'category')}),
        ('Дополнительноe', {'fields': ('comment', 'votings_count')}),
        ('Модерация', {'fields': ('is_banned',)}),
        ('Информация о видео', {
            'fields': ('title', 'pub_date', 'duration', 'preview_url',)
        }),
        ('Канал', {'fields': ('channel_name',)}),
        ('Статистика', {
            'fields': ('views_count', 'likes_count', 'comments_count')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            votings_count=Count('votes')
        ).order_by('-votings_count')

    @admin.display(description='Автор')
    def author(self, obj):
        return obj.user.username

    @admin.display(description='Голоса', ordering='votings_count')
    def votings_count(self, obj):
        return obj.votings_count
