from django import forms
from django.forms import inlineformset_factory
from .models import Horse, Medicine, Schedule, CalendarEvent
from django.core.exceptions import ValidationError
import datetime


class MedicineForm(forms.ModelForm):

    class Meta:
        model = Medicine
        fields = ('name', 'notes',)


class HorseForm(forms.ModelForm):
    """
    Age is in months.
    """
    class Meta:
        model = Horse
        fields = (
            'age',
            'weight',
            'dob',
            'name',
            'notes',
            'gender',
            'pregnant',
        )
        error_messages = {
            'age': {"error": ("Age cannot be negative or empty.")},
            'weight': {"error": ("Weight cannot be negative or empty.")},
            'dob': {"error": ("Date of Birth cannot be in the future.")},
            'name': {"error": ("Name cannot be empty.!")},
            'notes': {"error": ("Invalid characters in notes.")},
            'gender': {"error": ("Invalid gender.")},
            'pregnant': {"error": ("Invalid pregnancy.")},
        }

    def clean(self):
        cleaned_data = super(HorseForm, self).clean()
        if cleaned_data.get("dob") > datetime.date.today():
            self.add_error("dob", self.fields['dob'].error_messages['error'])
            raise ValidationError(self.fields['dob'].error_messages['error'])
        return cleaned_data


class ScheduleForm(forms.ModelForm):

    class Meta:
        model = Schedule
        fields = (
            'frequency',
            'interval',
            'classification',
            'doses',
        )

    def clean(self):
        cleaned_data = super(ScheduleForm, self).clean()
        return cleaned_data

class CalendarForm(forms.ModelForm):

    class Meta:
        model = CalendarEvent
        fields = (
            'title',
            'start',
            'end',
            'all_day'
        )

    def clean(self):
        cleaned_data = super(CalendarForm, self).clean()
        if cleaned_data.get('start') > cleaned_data.get('end'):
            self.add_error("start", "End date must be after start date.")
            self.add_error("end", "End date must be after start date.")
            raise ValidationError('End date must be after start date')
        return cleaned_data


ScheduleFormSet = inlineformset_factory(
    Medicine,
    Schedule,
    fields=(
        'frequency',
        'interval',
        'classification',
        'doses',
    ),
    extra=2,
)
