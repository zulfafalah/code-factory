from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import SocialComment

@admin.register(SocialComment)
class SocialCommentAdmin(ModelAdmin):
    list_display = ["nickname", "username", "platform", "created_at", "updated_at"]
    list_filter = ["platform"]
    search_fields = ["nickname", "username", "comment"]
    ordering = ["-created_at"]
    readonly_fields = ["created_at", "updated_at", "created_by", "updated_by"]

    def save_model(self, request, obj, form, change):
        if not change:  # Creating a new object
            obj.created_by = str(request.user)
        obj.updated_by = str(request.user)
        super().save_model(request, obj, form, change)

    fieldsets = (
        ("General", {
            "fields": (
                "comment",
                "platform",
            ),
            "classes": ("tabs",),
        }),
        ("User Info", {
            "fields": (
                "nickname",
                "username",
                "external_uid",
                "external_unique_id",
            ),
            "classes": ("tabs",),
        }),
        ("Avatar", {
            "fields": (
                "avatar_uri",
                "avatar_url_list",
                "avatar_url_prefix",
            ),
            "classes": ("tabs",),
        }),
        ("Audit", {
            "fields": (
                "created_by",
                "updated_by",
                "created_at",
                "updated_at",
            ),
            "classes": ("tabs",),
        }),
    )
