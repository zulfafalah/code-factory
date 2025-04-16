from django.db import models
from django.utils.translation import gettext as _

from master.models import Item
from master.models import TimeStampedModel
from palpal.utils import generate_nameming_series

from .task import run_scraper


# Create your models here.
class SalesOrder(TimeStampedModel):
    class StatusChoices(models.TextChoices):
        NOT_STARTED = "not_started", _("Not Started")
        COMPLETE = "complete", _("Complete")
        PENDING = "pending", _("Pending")
        REFUND = "refund", _("Refund")

    order_id = models.CharField(_("Order ID"), max_length=50)
    service_name = models.ForeignKey(
        Item, verbose_name=_("Service Name"), on_delete=models.CASCADE
    )
    date = models.DateTimeField(_("Date"), auto_now_add=True)
    status_order = models.CharField(
        _("Status"),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.NOT_STARTED,
    )
    is_refund = models.BooleanField(_("Is Refund"), default=False)
    file_data = models.CharField(_("File Data"), max_length=255, null=True, blank=True)

    def __str__(self):
        return self.order_id

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if not self.order_id:
            self.order_id = generate_nameming_series("SO")

        super().save(*args, **kwargs)
        if is_new:
            run_scraper.delay(self.order_id)
