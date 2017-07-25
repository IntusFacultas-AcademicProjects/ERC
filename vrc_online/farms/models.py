from django.db import models
from session.models import Profile


class Farm(models.Model):
    """
    A user can have many farms, a farm can have many horses
    """
    name = models.CharField("Name", max_length=32)
    address = models.TextField(
        "Address", max_length=256, blank=True, null=True)
    profile = models.ForeignKey(Profile,
                                on_delete=models.CASCADE,
                                related_name="farms"
                                )
