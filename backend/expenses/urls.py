from django.urls import path

from .views import GroupDetailView, GroupListCreateView, JoinGroupView

urlpatterns = [
    path('groups/', GroupListCreateView.as_view()),
    path('groups/<int:pk>/', GroupDetailView.as_view()),
    path('join/<str:code>/', JoinGroupView.as_view()),
]