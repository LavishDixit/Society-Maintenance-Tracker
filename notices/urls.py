from django.urls import path
from . import views

app_name = 'notices'

urlpatterns = [
    path('', views.notice_board, name='notice_board'),
    path('post/', views.post_notice, name='post_notice'),
]
