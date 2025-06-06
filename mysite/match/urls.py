from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('groups/', views.groups_view, name='groups'),
    path('groups/create/', views.create_group_view, name='create_group'),
    path('events/', views.events_view, name='events'),
    path('events/create/', views.create_event_view, name='create_event'),
    path('groups/<int:group_id>/matches/', views.group_match_recommendations, name='group_matches'),
] 