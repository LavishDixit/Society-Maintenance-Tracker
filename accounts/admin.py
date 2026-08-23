from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class SocietyUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Society info', {'fields': ('wing', 'flat_number', 'phone_number', 'is_committee')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Society info', {'fields': ('wing', 'flat_number', 'phone_number', 'is_committee')}),
    )
    list_display = ('username', 'email', 'wing', 'flat_number', 'is_committee', 'is_staff')
    list_filter = ('is_committee', 'is_staff', 'is_active', 'wing')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'flat_number', 'wing')
