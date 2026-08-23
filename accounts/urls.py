from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('login/', views.SocietyLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('directory/', views.resident_directory, name='resident_directory'),
    path('directory/export/', views.export_residents_csv, name='export_residents_csv'),
]
