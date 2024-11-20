from django.db import models
from django.utils.translation import gettext_lazy as _

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
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')
        ordering = ['tag_name']

    def __str__(self):
        return self.tag_name


class Category(TimeStampedModel):
    category_name = models.CharField(_("Category Name"), max_length=100)

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ['category_name']
    
    def __str__(self):
        return self.category_name
    

class Cookie(TimeStampedModel):
    cookie_data = models.JSONField(_("Cookie Data"), default=dict)

    class Meta:
        verbose_name = _('Cookie')
        verbose_name_plural = _('Cookies')
        ordering = ['cookie_data']

    def __str__(self):
        return str(self.cookie_data)
    

class ItemGroup(TimeStampedModel):
    group_name = models.CharField(_("Group Name"), max_length=255)
    description = models.TextField(_("Description"))
    icon = models.ImageField(_("Icon"), upload_to=None, height_field=None, width_field=None, max_length=None)
    slug = models.SlugField(_("Slug"))
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='category',
        verbose_name=_('Category'),
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.PROTECT,
        related_name='tag',
        verbose_name=_('Tag'),
    )
    cookie = models.ForeignKey(
        Cookie,
        on_delete=models.PROTECT,
        related_name='cookie',
        verbose_name=_('Cookie'),
    )

    class Meta:
        verbose_name = _('Item Group')
        verbose_name_plural = _('Item Groups')
        ordering = ['group_name']

    def __str__(self):
        return self.group_name
    

class Item(TimeStampedModel):
    item_name = models.CharField(_("Item Name"), max_length=255)
    description = models.TextField(_("Description"))
    json_property = models.JSONField(_("JSON Property"), default=dict,)
    slug = models.SlugField(_("slug"))
    group = models.ForeignKey(
        ItemGroup,
        on_delete=models.PROTECT,
        related_name='items',
        verbose_name=_('Item Group'),
    )

    class Meta:
        verbose_name = _('Item')
        verbose_name_plural = _('Items')
        ordering = ['item_name']
        indexes = [
            models.Index(fields=['group', 'item_name']),
        ]

    def __str__(self):
        return self.item_name

