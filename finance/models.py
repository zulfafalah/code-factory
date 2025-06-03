from django.db import models
from django.db.models import CharField, DateTimeField, DecimalField
from django.utils.translation import gettext_lazy as _

class GLEntry(models):
    voucher_type = CharField(_("Voucher Type"), max_length=255)
    voucher_no = CharField(_("Vouceher No"), max_length=255)
    posting_date = DateTimeField(auto_now_add=True)
    debit_amount = DecimalField(max_digits=10, decimal_places=2)
    credit_amount = DecimalField(max_digits=10, decimal_places=2)
