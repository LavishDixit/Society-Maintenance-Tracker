from django.contrib import admin
from .models import Rule, Contact


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ('order', 'title')
    ordering = ('order',)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'designation', 'phone_number')
    list_filter = ('category',)
