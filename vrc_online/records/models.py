from django.db import models
from django.utils.translation import ugettext_lazy as _
from farms.models import Farm


class Horse(models.Model):
    """
    Necessary fields:
        age (in months), dob, name, gender, pregnant
    Optional fields:
        weight, notes
    """
    STALLION = 0
    MARE = 1
    NOT_PREGNANT = 0
    PREGNANT = 1
    GENDER_CHOICES = (
        (STALLION, "Stallion"),
        (MARE, "Mare"),
    )
    PREGNANCY_CHOICES = (
        (NOT_PREGNANT, "Not Pregnant"),
        (PREGNANT, "Pregnant"),
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
    gender = models.IntegerField(
        "Gender", default=STALLION, choices=GENDER_CHOICES)
    pregnant = models.IntegerField(
        "Pregnant",
        default=NOT_PREGNANT,
        choices=PREGNANCY_CHOICES
    )
    sold = models.BooleanField("Sold", default=False)
    sale_price = models.IntegerField("Sale Price", blank=True, null=True)
    farm = models.ForeignKey(
        Farm,
        on_delete=models.CASCADE,
        related_name="horses",
        blank=True,
        null=True
    )

    def save(self, force_insert=False, force_update=False):
        is_new = self.id is None
        super(Horse, self).save(force_insert, force_update)
        if is_new:
            MedicalHistory.objects.create(horse=self)

    def __str__(self):
        gender = "Mare" if self.gender else "Stallion"
        return "ID {} | NAME: {} | GENDER: {} | WEIGHT: {} | AGE: {}".format(
            self.id,
            self.name,
            gender,
            self.weight,
            self.age
        )


class Medicine(models.Model):
    """
    A horse can have many medicines, and a medicine can be associated with many
    horses. A medicine can have many schedules.
    """
    WEEKS = 0
    MONTHS = 1
    YEARS = 2
    FOALS = 0
    ADULTS = 1
    PREGNANT = 2
    ALL = 3
    INTERVAL_CHOICES = (
        (WEEKS, "Weeks"),
        (MONTHS, "Months"),
        (YEARS, "Years"),
    )
    DEMOGRAPHIC_CHOICES = (
        (ALL, "All"),
        (FOALS, "Foals"),
        (ADULTS, "Adults"),
        (PREGNANT, "Pregnant Mares"),
    )

    # Fields unique to temporary medicines
    frequency = models.PositiveIntegerField("Frequency", blank=True, null=True)
    interval = models.IntegerField(
        "Interval", choices=INTERVAL_CHOICES, blank=True, null=True)
    classification = models.PositiveIntegerField(
        "Demographic",
        choices=DEMOGRAPHIC_CHOICES, blank=True, null=True
    )
    doses = models.PositiveIntegerField("Doses", blank=True, null=True)
    date_to_start = models.DateField(blank=True, null=True)
    horse = models.ForeignKey(
        Horse,
        on_delete=models.CASCADE,
        related_name="temporary_medicines",
        blank=True,
        null=True
    )

    # Fields required for all medicines
    name = models.CharField(max_length=32)
    notes = models.TextField(max_length=256, blank=True, null=True)
    horses = models.ManyToManyField(Horse)

    def __str__(self):
        return "{} | {}".format(self.name, self.notes)


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
    medicine = models.ForeignKey(
        Medicine, on_delete=models.CASCADE, related_name="events",
        blank=True, null=True)

    class Meta:
        verbose_name = _('Event')
        verbose_name_plural = _('Events')

    def __unicode__(self):
        return self.title


class Schedule(models.Model):
    """
    A schedule will have a frequency and an interval (e.g. 2 weeks),
    and a number of doses (e.g. 2 doses separated by 2 weeks)
    """
    WEEKS = 0
    MONTHS = 1
    YEARS = 2
    FOALS = 0
    ADULTS = 1
    PREGNANT = 2
    ALL = 3
    INTERVAL_CHOICES = (
        (WEEKS, "Weeks"),
        (MONTHS, "Months"),
        (YEARS, "Years"),
    )
    DEMOGRAPHIC_CHOICES = (
        (ALL, "All"),
        (FOALS, "Foals"),
        (ADULTS, "Adults"),
        (PREGNANT, "Pregnant Mares"),
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
        msg = "Medicine: {} | Doses: {} | Frequency: {} | Interval: {} | Classification: {}".format(self.medicine.name,
                                                                                                    self.doses,
                                                                                                    self.frequency,
                                                                                                    self.interval,
                                                                                                    self.classification
                                                                                                    )
        return msg


class MedicalHistory(models.Model):
    horse = models.OneToOneField(
        Horse,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="history"
    )


class MedicalEvent(models.Model):
    """
    Generated for all vaccines that have passed date and for manual adding
    """
    msg = models.TextField("Details", max_length=256)
    date = models.DateField()
    history = models.ForeignKey(
        MedicalHistory, on_delete=models.CASCADE, related_name="events")
