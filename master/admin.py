from django.contrib import admin

from .models import Item
from .models import ItemGroup
from .models import Tag
from .models import Cookie

admin.site.register(Item)
admin.site.register(ItemGroup)
admin.site.register(Tag)
admin.site.register(Cookie)
