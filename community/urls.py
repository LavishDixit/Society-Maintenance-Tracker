from django.urls import path
from . import views

app_name = 'community'

urlpatterns = [
    path('rules/', views.rules_list, name='rules_list'),
    path('rules/add/', views.rule_add, name='rule_add'),
    path('rules/<int:pk>/edit/', views.rule_edit, name='rule_edit'),
    path('rules/<int:pk>/delete/', views.rule_delete, name='rule_delete'),

    path('contacts/', views.contacts_list, name='contacts_list'),
    path('contacts/add/', views.contact_add, name='contact_add'),
    path('contacts/<int:pk>/edit/', views.contact_edit, name='contact_edit'),
    path('contacts/<int:pk>/delete/', views.contact_delete, name='contact_delete'),
]
