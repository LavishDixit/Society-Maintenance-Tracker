from django.contrib import admin
from .models import Complaint, StatusLog


class StatusLogInline(admin.TabularInline):
    model = StatusLog
    extra = 0
    readonly_fields = ('status', 'note', 'actor', 'timestamp')
    can_delete = False


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'resident', 'status', 'priority', 'created_at', 'is_overdue')
    list_filter = ('category', 'status', 'priority')
    inlines = [StatusLogInline]


@admin.register(StatusLog)
class StatusLogAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'status', 'actor', 'timestamp')
    readonly_fields = ('complaint', 'status', 'actor', 'timestamp')
