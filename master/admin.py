from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Cookie
from .models import Item
from .models import ItemGroup
from .models import Tag


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ["tag_name", "created_at", "updated_at"]
    search_fields = ["tag_name"]
    ordering = ["tag_name"]


@admin.register(Cookie)
class CookieAdmin(ModelAdmin):
    list_display = ["name", "application", "domain", "is_active", "created_at"]
    list_filter = ["application", "is_active"]
    search_fields = ["name", "domain"]
    ordering = ["-created_at"]


@admin.register(ItemGroup)
class ItemGroupAdmin(ModelAdmin):
    list_display = ["group_name", "slug", "created_at", "updated_at"]
    search_fields = ["group_name"]
    prepopulated_fields = {"slug": ("group_name",)}
    filter_horizontal = ["tags"]
    ordering = ["group_name"]


@admin.register(Item)
class ItemAdmin(ModelAdmin):
    list_display = ["item_name", "group", "slug", "created_at", "updated_at"]
    list_filter = ["group"]
    search_fields = ["item_name", "group__group_name"]
    prepopulated_fields = {"slug": ("item_name",)}
    ordering = ["item_name"]

