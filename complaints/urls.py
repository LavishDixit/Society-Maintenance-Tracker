from django.urls import path
from . import views

app_name = 'complaints'

urlpatterns = [
    path('redirect/', views.redirect_after_login, name='redirect_after_login'),

    # Resident
    path('raise/', views.raise_complaint, name='raise_complaint'),
    path('mine/', views.my_complaints, name='my_complaints'),
    path('<int:pk>/', views.complaint_detail, name='complaint_detail'),

    # Admin
    path('admin/', views.admin_complaint_list, name='admin_list'),
    path('admin/<int:pk>/update/', views.admin_complaint_update, name='admin_update'),
]
