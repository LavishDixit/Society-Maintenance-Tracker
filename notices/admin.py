from django.contrib import admin
from .models import Notice


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_important', 'author', 'created_at')
    list_filter = ('is_important',)
