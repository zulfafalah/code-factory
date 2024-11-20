from django.contrib import admin

from .models import Category
from .models import Cookie
from .models import Item
from .models import ItemGroup
from .models import Tag

admin.site.register(Item)
admin.site.register(ItemGroup)
admin.site.register(Tag)
admin.site.register(Category)
admin.site.register(Cookie)
