from django.db import models
from django.contrib.auth.models import User


class Farm(models.Model):
    """
    A user can have many farms, a farm can have many horses
    """
    name = models.CharField("Name", max_length=32)
    address = models.TextField(
        "Address", max_length=256, blank=True, null=True)
    user = models.ForeignKey(User)
