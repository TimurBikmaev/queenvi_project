from django.contrib.auth.views import LogoutView
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api import views


router_v1 = DefaultRouter()
router_v1.register('users', views.UserViewSet, basename='users')
# router_v1.register('posts', views.PostViewSet, basename='posts')
# router_v1.register(
#     r'posts/(?P<post_id>\d+)/comments', views.CommentViewSet, basename='comments'
# )
# router_v1.register('reports', views.ReportViewSet, basename='reports')
# router_v1.register('videos', views.VideoViewSet, basename='videos')

urlpatterns = [
    path('v1/', include(router_v1.urls)),
    path('v1/users/logout/', LogoutView.as_view(), name='logout'),
]
