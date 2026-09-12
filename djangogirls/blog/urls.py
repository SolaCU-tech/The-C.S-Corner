from django.urls import path
from . import views
urlpatterns = [
    path('', views.post_list, name='post_list'),
    path('post/new/', views.post_new, name='post_new'),
    path('post/<slug:slug>/', views.post_detail, name='post_detail'),
    path('drafts/', views.post_draft_list, name='post_draft_list'),
    path('post/<int:pk>/edit/', views.post_edit, name='post_edit'),
    path('post/<int:pk>/publish/', views.post_publish, name='post_publish'),
    path('post/<int:pk>/remove/', views.post_remove, name='post_remove'),
    path('comment/<int:pk>/remove/', views.comment_remove, name='comment_remove'),
    path('signup/', views.signup, name='signup'),
    path('post/<int:pk>/like/', views.post_react, {'value': 'like'}, name='post_like'),
    path('post/<int:pk>/dislike/', views.post_react, {'value': 'dislike'}, name='post_dislike'),
    path('posts/more/', views.post_more, name='post_more'),
    path('search/', views.search, name='search'),
    path('u/edit/', views.profile_edit, name='profile_edit'),
    path('u/<str:username>/follow/', views.follow_toggle, name='follow_toggle'),
    path('u/<str:username>/', views.user_profile, name='user_profile'),
]
