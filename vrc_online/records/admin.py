from django.contrib import admin
from .models import Horse, Schedule, Medicine
# Register your models here.
admin.site.register(Horse)
admin.site.register(Medicine)
admin.site.register(Schedule)

# Tweak admin site settings like title, header, 'View Site' URL, etc
admin.site.site_title = 'ERC Admin'
admin.site.site_header = 'ERC Administration'
