from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api import views
from core.constants import PublicIdConstants


router_v1 = DefaultRouter()
router_v1.register('profile', views.UserViewSet, basename='profile')
router_v1.register('posts', views.PostViewSet, basename='posts')
router_v1.register(
    rf'posts/(?P<post_id>{PublicIdConstants.URL_REGEX})/comments',
    views.CommentViewSet,
    basename='comments'
)
router_v1.register('reports', views.ReportViewSet, basename='reports')
router_v1.register('videos', views.VideoViewSet, basename='videos')


urlpatterns = [
    path('v1/profile/logout/', views.LogoutAPIView.as_view(), name='logout'),
    path('v1/', include(router_v1.urls)),
]
