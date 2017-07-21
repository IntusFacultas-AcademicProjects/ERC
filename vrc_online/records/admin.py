from django.contrib import admin
from .models import Horse, Schedule, Medicine
# Register your models here.
admin.site.register(Horse)
admin.site.register(Medicine)
admin.site.register(Schedule)
