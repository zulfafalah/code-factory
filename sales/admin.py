from django.contrib import admin

from .models import SalesOrder


@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ["order_id", "service_name", "date", "status_order"]
    readonly_fields = ["order_id", "status_order", "is_refund", "file_data"]
