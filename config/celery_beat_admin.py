"""
Django Celery Beat Admin with Unfold Theme

This module registers django_celery_beat models with Unfold's ModelAdmin
to provide a consistent admin theme across all admin pages.
"""

from django import forms
from django.contrib import admin
from unfold.admin import ModelAdmin

from celery import current_app
from django_celery_beat.models import (
    ClockedSchedule,
    CrontabSchedule,
    IntervalSchedule,
    PeriodicTask,
    SolarSchedule,
)


def get_registered_tasks():
    """Get all registered Celery tasks as choices for dropdown."""
    # Force Celery to load all tasks
    current_app.loader.import_default_modules()
    tasks = list(sorted(current_app.tasks.keys()))
    # Filter out internal celery tasks
    tasks = [t for t in tasks if not t.startswith('celery.')]
    return [('', '---------')] + [(task, task) for task in tasks]


class PeriodicTaskForm(forms.ModelForm):
    """Custom form for PeriodicTask with task dropdown."""
    
    task = forms.ChoiceField(
        choices=[],
        required=True,
        help_text="Select a registered Celery task",
        widget=forms.Select(attrs={
            'class': 'border bg-white font-medium rounded-md shadow-sm text-font-default-light text-sm focus:ring focus:ring-primary-300 focus:border-primary-600 focus:outline-none w-full dark:bg-base-900 dark:border-base-700 dark:text-font-default-dark dark:focus:border-primary-600 dark:focus:ring-primary-700 px-3 py-2 max-w-2xl'
        }),
    )
    
    class Meta:
        model = PeriodicTask
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically populate task choices
        self.fields['task'].choices = get_registered_tasks()


# Unregister the default admin classes
admin.site.unregister(ClockedSchedule)
admin.site.unregister(CrontabSchedule)
admin.site.unregister(IntervalSchedule)
admin.site.unregister(PeriodicTask)
admin.site.unregister(SolarSchedule)


@admin.register(ClockedSchedule)
class ClockedScheduleAdmin(ModelAdmin):
    """Admin for Clocked Schedule with Unfold theme."""
    list_display = ["clocked_time"]
    search_fields = ["clocked_time"]


@admin.register(CrontabSchedule)
class CrontabScheduleAdmin(ModelAdmin):
    """Admin for Crontab Schedule with Unfold theme."""
    list_display = [
        "minute",
        "hour",
        "day_of_week",
        "day_of_month",
        "month_of_year",
        "timezone",
    ]
    search_fields = ["minute", "hour"]
    list_filter = ["timezone"]


@admin.register(IntervalSchedule)
class IntervalScheduleAdmin(ModelAdmin):
    """Admin for Interval Schedule with Unfold theme."""
    list_display = ["every", "period"]
    search_fields = ["every"]
    list_filter = ["period"]


@admin.register(PeriodicTask)
class PeriodicTaskAdmin(ModelAdmin):
    """Admin for Periodic Task with Unfold theme."""
    form = PeriodicTaskForm
    
    list_display = [
        "name",
        "task",
        "enabled",
        "interval",
        "crontab",
        "clocked",
        "one_off",
        "start_time",
        "last_run_at",
    ]
    list_filter = ["enabled", "one_off", "interval", "crontab"]
    search_fields = ["name", "task"]
    ordering = ["name"]
    readonly_fields = ["last_run_at", "total_run_count", "date_changed"]
    
    fieldsets = (
        ("Basic Information", {
            "fields": (
                "name",
                "task",
                "enabled",
            ),
        }),
        ("Schedule", {
            "fields": (
                "interval",
                "crontab",
                "clocked",
                "solar",
                "one_off",
                "start_time",
                "expires",
            ),
            "description": "Set the schedule for your task. Choose only one schedule type.",
        }),
        ("Arguments", {
            "fields": (
                "args",
                "kwargs",
            ),
            "description": "Arguments to pass to the task (JSON format).",
        }),
        ("Execution Options", {
            "fields": (
                "queue",
                "exchange",
                "routing_key",
                "headers",
                "priority",
                "expire_seconds",
            ),
            "classes": ("collapse",),
        }),
        ("Run Information", {
            "fields": (
                "last_run_at",
                "total_run_count",
                "date_changed",
                "description",
            ),
        }),
    )


@admin.register(SolarSchedule)
class SolarScheduleAdmin(ModelAdmin):
    """Admin for Solar Schedule with Unfold theme."""
    list_display = ["event", "latitude", "longitude"]
    list_filter = ["event"]
    search_fields = ["event"]
