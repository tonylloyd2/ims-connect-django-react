from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import views
from .search_views import SearchViewSet

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'ideas', views.IdeaViewSet)
router.register(r'votes', views.VoteViewSet)
router.register(r'teams', views.TeamViewSet)
router.register(r'documents', views.DocumentViewSet)
router.register(r'comments', views.CommentViewSet)
router.register(r'audit-logs', views.AuditLogViewSet)
router.register(r'notifications', views.NotificationViewSet, basename='notification')
router.register(r'milestones', views.MilestoneViewSet)
router.register(r'categories', views.CategoryViewSet)
router.register(r'search', SearchViewSet, basename='search')

urlpatterns = [
    path('', include(router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
