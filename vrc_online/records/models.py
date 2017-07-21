from django.db import models
from django.utils.translation import ugettext_lazy as _


class Horse(models.Model):
    """
    Necessary fields:
        age (in months), dob, name, gender, pregnant
    Optional fields:
        weight, notes
    """
    GENDER_CHOICES = (
        (0, "Stallion"),
        (1, "Mare"),
    )
    PREGNANCY_CHOICES = (
        (0, "Not Pregnant"),
        (1, "Pregnant"),
    )
    age = models.PositiveIntegerField("Age", default=0)
    weight = models.PositiveIntegerField(
        "Weight",
        default=0,
        blank=True,
        null=True
    )
    dob = models.DateField("Date of Birth")
    date_of_impregnation = models.DateField(
        "Date of Impregnation",
        blank=True,
        null=True
    )
    name = models.CharField("Name", max_length=32)
    notes = models.TextField("Notes", max_length=256, blank=True, null=True)
    gender = models.IntegerField("Gender", default=0, choices=GENDER_CHOICES)
    pregnant = models.IntegerField(
        "Pregnant",
        default=0,
        choices=PREGNANCY_CHOICES
    )

    def __str__(self):
        gender = "Mare" if self.gender else "Stallion"
        return "ID {} | NAME: {} | GENDER: {} | WEIGHT: {} | AGE: {}".format(
            self.id,
            self.name,
            gender,
            self.weight,
            self.age
        )


class CalendarEvent(models.Model):
    """The event set a record for an
    activity that will be scheduled at a
    specified date and time.

    It could be on a date and time
    to start and end, but can also be all day.

    :param title: Title of event
    :type title: str.

    :param start: Start date of event
    :type start: datetime.

    :param end: End date of event
    :type end: datetime.

    :param all_day: Define event for all day
    :type all_day: bool.
    """
    title = models.CharField(_('Title'), blank=True, max_length=200)
    start = models.DateTimeField(_('Start'))
    end = models.DateTimeField(_('End'))
    all_day = models.BooleanField(_('All day'), default=False)
    horse = models.ForeignKey(
        Horse,
        on_delete=models.CASCADE,
        related_name="events",
        null=True,
    )

    class Meta:
        verbose_name = _('Event')
        verbose_name_plural = _('Events')

    def __unicode__(self):
        return self.title


class Medicine(models.Model):
    """
    A horse can have many medicines, and a medicine can be associated with many
    horses. A medicine can have many schedules.
    """
    name = models.CharField(max_length=32)
    notes = models.TextField(max_length=256, blank=True, null=True)
    horses = models.ManyToManyField(Horse)

    def __str__(self):
        return "{} | {}".format(self.name, self.notes)


class Schedule(models.Model):
    """
    A schedule will have a frequency and an interval (e.g. 2 weeks),
    and a number of doses (e.g. 2 doses separated by 2 weeks)
    """
    INTERVAL_CHOICES = (
        (0, "Weeks"),
        (1, "Months"),
        (2, "Years"),
    )
    DEMOGRAPHIC_CHOICES = (
        (0, "Foals"),
        (1, "Adults"),
        (2, "Pregnant Mares"),
    )
    frequency = models.PositiveIntegerField("Frequency", default=0)
    interval = models.IntegerField("Interval", choices=INTERVAL_CHOICES)
    classification = models.PositiveIntegerField(
        "Demographic",
        choices=DEMOGRAPHIC_CHOICES
    )
    doses = models.PositiveIntegerField("Doses", default=0)
    medicine = models.ForeignKey(
        'Medicine',
        on_delete=models.CASCADE,
        related_name="schedules"
    )

    def __str__(self):
        return "Medicine: {} | Doses: {} | Frequency: {} | " \
            + "Interval: {} | Classification: {}".format(
                self.medicine.name,
                self.doses,
                self.frequency,
                self.interval,
                self.classification
            )
