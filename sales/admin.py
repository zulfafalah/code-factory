from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import SalesOrder


@admin.register(SalesOrder)
class SalesOrderAdmin(ModelAdmin):
    list_display = ["order_id", "service_name", "date", "status_order"]
    list_filter = ["status_order", "is_refund"]
    search_fields = ["order_id"]
    readonly_fields = ["order_id", "status_order", "is_refund", "file_data"]
    ordering = ["-date"]

