from itertools import chain
import datetime
from dateutil import relativedelta
# from fullcalendar.models import CalendarEvent
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import View
from django.contrib import messages
from django.db.models import Q

from fullcalendar.util import events_to_json, calendar_options
from calendar import monthrange
from records.forms import MedicineForm, HorseForm, ScheduleFormSet
from records.models import Medicine, Horse, CalendarEvent

OPTIONS = """{  timeFormat: "H:mm",
                header: {
                    left: 'prev,next today',
                    center: 'title',
                    right: 'month,agendaWeek,agendaDay',
                },
                allDaySlot: false,
                firstDay: 0,
                weekMode: 'liquid',
                slotMinutes: 15,
                defaultEventMinutes: 30,
                minTime: 0,
                maxTime: 24,
                height: 600,
                editable: true,
                eventLimit: true,
                dayClick: function(date, allDay, jsEvent, view) {
                    if (allDay) {
                        $('#calendar').fullCalendar('gotoDate', date)
                        $('#calendar').fullCalendar('changeView', 'agendaDay')
                    }
                },
                eventClick: function(event, jsEvent, view) {
                    if (view.name == 'month') {
                        $('#calendar').fullCalendar('gotoDate', event.start)
                        $('#calendar').fullCalendar('changeView', 'agendaDay')
                    }
                },
            }"""


def index(request):
    """
    Uses Django port for fullcalendar. Landing page with calendar, actions and
    day at a glance.
    Template: index.html
    """
    event_url = 'all_events/'
    today = datetime.date.today()
    return render(
        request,
        'records/index.html',
        {
            'calendar_config_options': calendar_options(event_url, OPTIONS),
            "today": today,
        }
    )


def all_events(request):
    """
    JSON endpoint for all calendar events.
    """
    events = CalendarEvent.objects.all()
    return HttpResponse(
        events_to_json(events),
        content_type='application/json'
    )


class MedicineList(View):

    def get(self, request):
        medicines = Medicine.objects.all()
        parameters = request.GET.copy()
        parameters = {k: v for k, v in parameters.items() if v}
        keyword = parameters.get("keyword", None)
        frequency = parameters.get("frequency", None)
        doses = parameters.get("doses", None)
        interval = parameters.get("interval", None)
        classification = parameters.get("classification", None)
        if keyword is not None:
            medicines = medicines.filter(Q(name__icontains=keyword) |
                                   Q(notes__icontains=keyword))
        if frequency is not None:
            medicines = medicines.filter(schedules__frequency=frequency)
        if doses is not None:
            medicines = medicines.filter(schedules__doses=doses)
        if interval is not None:
            if interval != "":
                medicines = medicines.filter(schedules__interval=interval)
        if classification is not None:
            if classification != "":
                medicines = medicines.filter(
                    schedules__classification=classification)
        schedules = {}
        for medicine in medicines:
            schedules[medicine.id] = medicine.schedules.all()
        return render(
            request,
            'records/medicine_list.html',
            {
                "medicines": medicines,
                "keyword": keyword,
                "frequency": frequency,
                "doses": doses,
                "interval": interval,
                "classification": classification,
                "schedules": schedules,
            }
        )


class MedicineView(View):

    def get(self, request, pk):
        medicine = Medicine.objects.get(pk=pk)
        schedules = medicine.schedules.all()
        form = MedicineForm(instance=medicine)
        formset = ScheduleFormSet(instance=medicine)
        return render(request,
                      'records/medicine_view.html',
                      {
                          "form": form,
                          "medicine": medicine,
                          "schedules": schedules,
                          "formset": formset,
                      }
                      )

    def post(self, request, pk):
        medicine = Medicine.objects.get(pk=pk)
        parameters = request.POST.copy()
        del parameters['csrfmiddlewaretoken']
        if parameters.get("_method") == "MEDICINE":
            del parameters['_method']
            form = MedicineForm(parameters)
            if not form.is_valid():
                schedules = medicine.schedules.all()
                formset = ScheduleFormSet(instance=medicine)
                return render(request,
                              'records/medicine_view.html',
                              {
                                  "form": form,
                                  "medicine": medicine,
                                  "schedules": schedules,
                                  "formset": formset,
                              }
                              )
            medicine.name = parameters.get("name")
            medicine.notes = parameters.get("notes")
            medicine.save()
            messages.success(request, "Medicine successfully updated.")
            return HttpResponseRedirect(
                reverse_lazy('records:review-medicine', kwargs={"pk": pk})
            )
        elif parameters.get("_method") == "EDIT_SCHEDULES":
            del parameters['_method']
            print(parameters)
            formset = ScheduleFormSet(parameters, instance=medicine)
            if formset.is_valid():
                formset.save()
                messages.success(request, "Schedules successfully updated.")
                return HttpResponseRedirect(
                    reverse_lazy('records:review-medicine', kwargs={"pk": pk})
                )
            schedules = medicine.schedules.all()
            form = MedicineForm(instance=medicine)
            return render(request,
                          'records/medicine_view.html',
                          {
                              "form": form,
                              "medicine": medicine,
                              "schedules": schedules,
                              "formset": formset,
                          }
                          )


class CreateMedicine(View):
    """
    Create Medicine Form, segues to schedule creation form.
    Template: medicine_form.html
    """

    def post(self, request):
        form = MedicineForm(request.POST)

        if not form.is_valid():
            return render(
                request,
                'records/medicine_form.html',
                {
                    "form": form,
                }
            )
        med = form.save()
        messages.success(request, "Medicine successfully created.")
        return HttpResponseRedirect(reverse_lazy('records:add-schedules',
                                                 kwargs={'pk': med.id}))

    def get(self, request):
        form = MedicineForm()
        return render(
            request,
            'records/medicine_form.html',
            {
                "form": form,
            }
        )


class CreateSchedule(View):
    """
    Create applications for a just-created medication.
    Template: schedule_form.html
    """

    def post(self, request, pk):
        med = Medicine.objects.get(pk=pk)

        # Used for example text.
        date1 = datetime.date.today() + datetime.timedelta(7)
        date2 = datetime.date.today() + datetime.timedelta(14)
        formset = ScheduleFormSet(request.POST, instance=med)
        if not formset.is_valid():
            return render(
                request,
                'records/schedule_form.html',
                {
                    "med": med,
                    "formset": formset,
                    "date1": date1,
                    "date2": date2,
                }
            )
        formset.save()
        messages.success(
            request,
            "Schedules successfully attached to medicine."
        )
        return HttpResponseRedirect(reverse_lazy('records:index'))

    def get(self, request, pk):
        med = Medicine.objects.get(pk=pk)
        date1 = datetime.date.today() + datetime.timedelta(7)
        date2 = datetime.date.today() + datetime.timedelta(14)
        formset = ScheduleFormSet(instance=med)
        return render(
            request,
            'records/schedule_form.html',
            {
                "med": med,
                "formset": formset,
                "date1": date1,
                "date2": date2,
            }
        )


def delete_medicine(request, pk):
    medicine = Medicine.objects.get(pk=pk)
    if medicine:
        medicine.delete()
        messages.success(request, "Medicine successfully deleted.")
        return HttpResponseRedirect(reverse_lazy("records:medicine-list"))
    messages.error(request, "Medicine does not exist.")
    return HttpResponseRedirect(reverse_lazy("records:medicine-list"))


class HorseList(View):

    def get(self, request):
        horses = Horse.objects.all()
        parameters = request.GET.copy()
        parameters = {k: v for k, v in parameters.items() if v}
        keyword = parameters.get("keyword", None)
        weight_lower = parameters.get("weight_lower", None)
        weight_upper = parameters.get("weight_upper", None)
        gender = parameters.get("gender", None)
        pregnant = parameters.get("pregnant", None)
        upper_age = parameters.get("lower_age", None)
        lower_age = parameters.get("upper_age", None)
        age_class = parameters.get("age_class", None)
        start = parameters.get("start", None)
        end = parameters.get("end", None)
        if keyword is not None:
            horses = horses.filter(Q(name__icontains=keyword) |
                                   Q(notes__icontains=keyword))
        if weight_lower is not None:
            if weight_upper is not None:
                horses = horses.filter(
                    weight__range=[int(weight_lower), int(weight_upper)])
            else:
                horses = horses.filter(
                    weight__gte=int(weight_lower))
        elif weight_upper is not None:
            horses = horses.filter(weight__lte=int(weight_upper))
        if gender is not None:
            if gender != "":
                horses = horses.filter(gender=gender)
        if pregnant is not None:
            if pregnant != "":
                horses = horses.filter(pregnant=pregnant)
        if lower_age is not None:
            if upper_age is not None:
                if int(age_class) == 0:
                    date_lower = datetime.datetime.today().date() - \
                        relativedelta.relativedelta(months=int(lower_age))
                    date_upper = datetime.datetime.today().date() - \
                        relativedelta.relativedelta(months=int(upper_age))
                    horses = horses.filter(dob__range=[date_lower, date_upper])
                else:
                    date_lower = datetime.datetime.today().date() - \
                        relativedelta.relativedelta(months=int(lower_age) * 12)
                    date_upper = datetime.datetime.today().date() - \
                        relativedelta.relativedelta(months=int(upper_age) * 12)
                    horses = horses.filter(dob__range=[date_lower, date_upper])
            else:
                if int(age_class) == 0:
                    date_lower = datetime.datetime.today().date() - \
                        relativedelta.relativedelta(months=int(lower_age))
                    horses = horses.filter(dob__gte=date_lower)
                else:
                    date_lower = datetime.datetime.today().date() - \
                        relativedelta.relativedelta(months=int(lower_age) * 12)
                    horses = horses.filter(dob__gte=date_lower)
        elif upper_age is not None:
            if int(age_class) == 0:
                date_upper = datetime.datetime.today().date() - \
                    relativedelta.relativedelta(months=int(upper_age))
                horses = horses.filter(dob__lte=date_upper)
            else:
                date_upper = datetime.datetime.today().date() - \
                    relativedelta.relativedelta(months=int(upper_age) * 12)
                horses = horses.filter(dob__lte=date_upper)
        if start is not None:
            start = datetime.datetime.strptime(start, '%m/%d/%Y').date()
            if end is not None:
                end = datetime.datetime.strptime(end, '%m/%d/%Y').date()
                horses = horses.filter(dob__range=[start, end])
            else:
                horses = horses.filter(dob__gte=start)
        elif end is not None:
            end = datetime.datetime.strptime(end, '%m/%d/%Y').date()
            horses = horses.filter(dob__lte=end)
        years = {}
        months = {}
        for horse in horses:
            years[horse.id] = int(horse.age / 12)
            months[horse.id] = horse.age % 12
        if start is not None:
            start = start.strftime("%m/%d/%Y")
        if end is not None:
            end = end.strftime("%m/%d/%Y")
        return render(
            request,
            'records/horse_list.html',
            {
                "horses": horses,
                "years": years,
                "months": months,
                "keyword": keyword,
                "weight_lower": weight_lower,
                "weight_upper": weight_upper,
                "gender": gender,
                "pregnant": pregnant,
                "upper_age": lower_age,
                "lower_age": upper_age,
                "age_class": age_class,
                "start": start,
                "end": end,
                "age_class": age_class,
            }
        )


class HorseView(View):

    def monthdelta(self, d1, d2):
        delta = 0
        while True:
            mdays = monthrange(d1.year, d1.month)[1]
            d1 += datetime.timedelta(days=mdays)
            if d1 <= d2:
                delta += 1
            else:
                break
        return delta

    def dob_convert(self, dob):
        month = dob[0:2]
        day = dob[3:5]
        year = dob[6:]
        return year + "-" + month + "-" + day

    def get(self, request, pk):
        horse = Horse.objects.get(pk=pk)
        medicines = horse.medicine_set.all()
        schedules = {}
        add_medicines = Medicine.objects.exclude(id__in=medicines)
        for medicine in medicines:
            schedules[medicine.id] = medicine.schedules.all()
        form = HorseForm(instance=horse)
        add_schedules = {}
        for medicine in add_medicines:
            add_schedules[medicine.id] = medicine.schedules.all()
        return render(request,
                      'records/horse_view.html',
                      {
                          "form": form,
                          "horse": horse,
                          "medicines": medicines,
                          "schedules": schedules,
                          "add_medicines": add_medicines,
                          "add_schedules": add_schedules,
                      }
                      )

    def post(self, request, pk):
        horse = Horse.objects.filter(pk=pk)
        parameters = request.POST.copy()
        del parameters['csrfmiddlewaretoken']
        if parameters.get("_method") == "HORSE":
            del parameters['_method']
            if parameters["gender"] == "0":
                parameters["pregnant"] = "0"
            dob = parameters.get("dob", 0)
            year = dob[6:]
            month = dob[0:2]
            day = dob[3:5]
            date = datetime.date(int(year), int(month), int(day))
            today = datetime.date.today()
            parameters['age'] = self.monthdelta(date, today)
            print(parameters)
            form = HorseForm(parameters)
            if not form.is_valid():
                print("Wrong!")
                print(form.errors)
                horse = Horse.objects.get(pk=pk)
                medicines = horse.medicine_set.all()
                schedules = {}
                add_medicines = Medicine.objects.all()
                for medicine in medicines:
                    schedules[medicine.id] = medicine.schedules.all()
                add_schedules = {}
                for medicine in add_medicines:
                    add_schedules[medicine.id] = medicine.schedules.all()
                return render(request,
                              'records/horse_view.html',
                              {
                                  "form": form,
                                  "horse": horse,
                                  "medicines": medicines,
                                  "schedules": schedules,
                                  "add_medicines": add_medicines,
                                  "add_schedules": add_schedules,
                              }
                              )
            print(horse)
            parameters["dob"] = self.dob_convert(parameters["dob"])
            horse.update(dob=parameters.get("dob"))
            horse.update(age=parameters.get("age"))
            horse.update(weight=parameters.get("weight"))
            horse.update(name=parameters.get("name"))
            horse.update(notes=parameters.get("notes"))
            horse.update(gender=parameters.get("gender"))
            horse.update(pregnant=parameters.get("pregnant"))
            print("AFTER")
            print(horse)
            messages.success(request, "Horse successfully updated.")
            return HttpResponseRedirect(
                reverse_lazy('records:review-horse', kwargs={"pk": pk})
            )
        elif parameters.get("_method") == "DELETE_MEDICINE":
            del parameters['_method']
            horse = Horse.objects.get(pk=pk)
            for key, value in parameters.items():
                medicine = Medicine.objects.get(pk=int(key))
                medicine.horses.remove(horse)
            messages.success(request, "Medicine successfully removed.")
            return HttpResponseRedirect(
                reverse_lazy('records:review-horse', kwargs={"pk": pk})
            )
        elif parameters.get("_method") == "ADD_MEDICINE":
            del parameters['_method']
            horse = Horse.objects.get(pk=pk)
            for key, value in parameters.items():
                medicine = Medicine.objects.get(pk=int(key))
                medicine.horses.add(horse)
            messages.success(request, "Medicine successfully added.")
            return HttpResponseRedirect(
                reverse_lazy('records:review-horse', kwargs={"pk": pk})
            )


class CreateHorse(View):
    """
    Create Horse form, segues to medicine application
    Template: horse_form.html
    """

    def monthdelta(self, d1, d2):
        delta = 0
        while True:
            mdays = monthrange(d1.year, d1.month)[1]
            d1 += datetime.timedelta(days=mdays)
            if d1 <= d2:
                delta += 1
            else:
                break
        return delta

    def post(self, request):
        parameters = request.POST.copy()
        dob = parameters.get("dob", 0)
        year = dob[6:]
        month = dob[0:2]
        day = dob[3:5]
        date = datetime.date(int(year), int(month), int(day))
        today = datetime.date.today()
        del parameters["csrfmiddlewaretoken"]
        print(parameters)
        parameters['age'] = self.monthdelta(date, today)
        if parameters["gender"] == "0":
            parameters["pregnant"] = "0"
        form = HorseForm(parameters)
        if not form.is_valid():
            return render(
                request,
                'records/horse_form.html',
                {
                    "form": form,
                }
            )
        horse = form.save()
        print(horse)
        messages.success(request, "Horse successfully created.")
        return HttpResponseRedirect(
            reverse_lazy('records:apply-medicine', kwargs={'pk': horse.id})
        )

    def get(self, request):
        form = HorseForm()
        return render(
            request,
            'records/horse_form.html',
            {
                "form": form,
            }
        )


class AddMedicine(View):
    """
    Add medicine to a horse immediately following horse creation.
    Template: add_medicine.html
    """

    def post(self, request, pk):
        parameters = request.POST.copy()
        print(parameters)
        del parameters['csrfmiddlewaretoken']
        horse = Horse.objects.get(pk=pk)
        for key, value in parameters.items():
            print(key)
            medicine = Medicine.objects.get(pk=int(key))
            medicine.horses.add(horse)
        if len(parameters) > 0:
            messages.success(request, "Successfully added medicines.")
        else:
            messages.success(
                request,
                "No medicines were added, submit was successful."
            )
        return HttpResponseRedirect(reverse_lazy('records:index'))

    def get(self, request, pk):
        medicine = Medicine.objects.all()
        horse = Horse.objects.get(pk=pk)
        months = 0
        years = 0
        schedules = {}
        for med in medicine:
            schedules[med.id] = med.schedules.all()
        if horse.age % 12 == 0:
            years = horse.age / 12
        else:
            months = horse.age % 12
            years = (horse.age - months) / 12
        return render(
            request,
            'records/add_medicine.html',
            {
                "medicines": medicine,
                "horse": horse,
                "years": years,
                "months": months,
                "schedules": schedules,
            }
        )


def delete_horse(request, pk):
    horse = Horse.objects.get(pk=pk)
    if horse:
        horse.delete()
        messages.success(request, "Horse successfully deleted.")
        return HttpResponseRedirect(reverse_lazy("records:horse-list"))
    messages.error(request, "Horse does not exist.")
    return HttpResponseRedirect(reverse_lazy("records:horse-list"))


class SearchList(View):

    def get(self, request):
        search_term = request.GET.get("search", None)
        horses = Horse.objects.none()
        medicines = Medicine.objects.none()
        if (search_term is not None and search_term.find(" ") > -1):
            search_term = search_term.split()
            for keyword in search_term:
                add = Horse.objects.filter(
                    Q(name__icontains=keyword) | Q(notes__icontains=keyword))
                horses = list(chain(horses, add))
            for keyword in search_term:
                add = Medicine.objects.filter(
                    Q(name__icontains=keyword) | Q(notes__icontains=keyword))
                medicines = list(chain(medicines, add))
        elif search_term is not None:
            horses = horses.filter(Q(name__icontains=search_term) |
                                   Q(notes__icontains=search_term))
            medicines = medicines.filter(Q(name__icontains=search_term) |
                                   Q(notes__icontains=search_term))
        distinct_horses = {}
        horse_keys = []
        distinct_medicines = {}
        medicine_keys = []
        for horse in horses:
            if horse.id not in distinct_horses:
                distinct_horses[horse.id] = horse
                horse_keys.append(horse.id)
        for medicine in medicines:
            if medicine.id not in distinct_medicines:
                distinct_medicines[medicine.id] = medicine
                medicine_keys.append(medicine.id)
        schedules = {}
        horses = Horse.objects.filter(pk__in=horse_keys)
        medicines = Medicine.objects.filter(pk__in=medicine_keys)
        for medicine in medicines:
            schedules[medicine.id] = medicine.schedules.all()
        years = {}
        months = {}
        for horse in horses:
            years[horse.id] = int(horse.age / 12)
            months[horse.id] = horse.age % 12
        return render(
            request,
            'records/search_results.html',
            {
                "horses": horses,
                "medicines": medicines,
                "schedules": schedules,
                "years": years,
                "months": months,
            }
        )
