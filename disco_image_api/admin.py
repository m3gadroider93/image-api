from django.contrib import admin
from . import models

# Register your models here.

admin.site.register(models.UserPlan)
admin.site.register(models.ThumbnailSize)
admin.site.register(models.Image)
admin.site.register(models.Plan)
