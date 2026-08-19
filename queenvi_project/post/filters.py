from django.utils import timezone
from django_filters import rest_framework as filters

from post.constants import FilterConstants as FC
from post.models import Post
from post.utils import FilterUtils


class PostFilter(filters.FilterSet):
    media = filters.CharFilter(
        field_name='media__file_type',
        lookup_expr='exact'
    )
    created = filters.CharFilter(method='filter_created')

    def filter_created(self, queryset, name, value):
        now = timezone.localtime()

        if value == 'today':
            start_of_day = now.replace(
                hour=FC.START_DAY_HOUR,
                minute=FC.START_DAY_MINUTE,
                second=FC.START_DAY_SECOND,
                microsecond=FC.START_DAY_MICROSECOND
            )
            return queryset.filter(created_at__gte=start_of_day)

        elif value == 'week':
            return FilterUtils.post_queryset(queryset, now, FC.DAYS_IN_WEEK)

        elif value == 'month':
            return FilterUtils.post_queryset(queryset, now, FC.DAYS_IN_MONTH)

        elif value == 'year':
            return FilterUtils.post_queryset(queryset, now, FC.DAYS_IN_YEAR)

        return queryset

    class Meta:
        model = Post
        fields = ['is_for_stream']
