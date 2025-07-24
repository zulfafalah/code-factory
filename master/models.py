from django.db import models
from django.utils.translation import gettext_lazy as _
import json


class TimeStampedModel(models.Model):
    """
    Abstract base model yang menyediakan self-updating
    created dan modified fields.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Tag(TimeStampedModel):
    tag_name = models.CharField(_("Tag"), max_length=100)

    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")
        ordering = ["tag_name"]

    def __str__(self):
        return self.tag_name


class Cookie(TimeStampedModel):
    """
    Model untuk menyimpan cookie dari berbagai aplikasi
    secara general dengan format JSON
    """

    APPLICATION_CHOICES = [
        ('youtube', _('YouTube')),
        ('instagram', _('Instagram')),
        ('shopee', _('Shopee')),
        ('tiktok', _('TikTok')),
        ('facebook', _('Facebook')),
        ('twitter', _('Twitter')),
        ('linkedin', _('LinkedIn')),
        ('other', _('Other')),
    ]

    name = models.CharField(_("Cookie Name"), max_length=255)
    application = models.CharField(
        _("Application"),
        max_length=50,
        choices=APPLICATION_CHOICES,
        default='other'
    )
    cookie_data = models.JSONField(
        _("Cookie Data"),
        help_text=_("JSON format cookie data from the application")
    )
    description = models.TextField(_("Description"), blank=True, null=True)
    is_active = models.BooleanField(_("Is Active"), default=True)
    user_agent = models.TextField(_("User Agent"), blank=True, null=True)
    domain = models.CharField(_("Domain"), max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = _("Cookie")
        verbose_name_plural = _("Cookies")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["application", "is_active"]),
            models.Index(fields=["domain", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_application_display()})"

    def clean(self):
        """
        Validasi untuk memastikan cookie_data adalah JSON yang valid
        """
        if self.cookie_data:
            try:
                if isinstance(self.cookie_data, str):
                    json.loads(self.cookie_data)
            except json.JSONDecodeError:
                from django.core.exceptions import ValidationError
                raise ValidationError(_("Cookie data must be valid JSON"))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        """
        Check apakah cookie sudah expired
        """
        if self.expires_at:
            from django.utils import timezone
            return timezone.now() > self.expires_at
        return False

    def get_cookie_count(self):
        """
        Mendapatkan jumlah cookie dalam cookie_data
        """
        if isinstance(self.cookie_data, dict):
            return len(self.cookie_data)
        elif isinstance(self.cookie_data, list):
            return len(self.cookie_data)
        return 0


class ItemGroup(TimeStampedModel):
    group_name = models.CharField(_("Group Name"), max_length=255)
    description = models.TextField(_("Description"))
    icon = models.ImageField(
        _("Icon"),
        upload_to="item-group",
        height_field=None,
        width_field=None,
        max_length=None,
    )
    slug = models.SlugField(_("Slug"), null=True, blank=True)
    tags = models.ManyToManyField(
        Tag,
        related_name="item_groups",
        verbose_name=_("Tags"),
    )
    cookie_data = models.JSONField(_("Cookie Data"), default=dict)

    class Meta:
        verbose_name = _("Item Group")
        verbose_name_plural = _("Item Groups")
        ordering = ["group_name"]

    def __str__(self):
        return self.group_name


class Item(TimeStampedModel):
    item_name = models.CharField(_("Item Name"), max_length=255)
    description = models.TextField(_("Description"))
    json_property = models.JSONField(_("JSON Property"), default=dict)
    slug = models.SlugField(_("slug"))
    group = models.ForeignKey(
        ItemGroup,
        on_delete=models.PROTECT,
        related_name="items",
        verbose_name=_("Item Group"),
    )

    class Meta:
        verbose_name = _("Item")
        verbose_name_plural = _("Items")
        ordering = ["item_name"]
        indexes = [
            models.Index(fields=["group", "item_name"]),
        ]

    def __str__(self):
        return self.item_name
