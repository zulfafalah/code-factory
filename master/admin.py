from django.contrib import admin
from .models import Item, ItemGroup, Tag, Category, Cookie

admin.site.register(Item)
admin.site.register(ItemGroup)
admin.site.register(Tag)
admin.site.register(Category)
admin.site.register(Cookie)
