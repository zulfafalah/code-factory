from django.db import models
from master.models import TimeStampedModel, Item
from django.utils.translation import _

# Create your models here.
class SalesOrder(TimeStampedModel):
    order_id = models.CharField(_("Order ID"), max_length=50)
    service_name = models.models.ForeignKey(Item, verbose_name=_("service_name"), on_delete=models.CASCADE)
    date = models.DateTimeField(_("Date"), auto_now_add=True)
    status = models.ForeignKey("StatusSalesOrder", verbose_name=_("Status"), on_delete=models.CASCADE)
    is_refund = models.BooleanField(_("is_refund"))
    file_data = models.CharField(_("File data"), max_length=255)


class StatusSalesOrder(models):
    status_name = models.CharField(_("Status"), max_length=100)