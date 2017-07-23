from itertools import chain
from datetime import date
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Q
from django.views import View
from fullcalendar.util import events_to_json, calendar_options
from records.models import CalendarEvent, Horse, Medicine


OPTIONS = """{  timeFormat: "H:mm",
                header: {
                    left: 'prev,next today',
                    center: 'title',
                    right: 'month,agendaWeek,agendaDay',
                },
                allDaySlot: true,
                firstDay: 0,
                weekMode: 'liquid',
                slotMinutes: 15,
                defaultEventMinutes: 30,
                minTime: 0,
                maxTime: 24,
                eventLimit: true,
                views: {
                     month: {
                       eventLimit: 3
                     }
                },
                height: 600,
                editable: false,
                eventLimit: true,
                eventLimitText: "More",
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


def print_today(request):
    today_events = CalendarEvent.objects.filter(
        start=date.today()).exclude(title__icontains="born")
    today = date.today()
    return render(
        request,
        'records/printable.html',
        {
            'events': today_events,
            'today': today,
        }
    )


def index(request):
    """
    Uses Django port for fullcalendar. Landing page with calendar, actions and
    day at a glance.
    Template: index.html
    """
    event_url = 'all_events/'
    today = date.today()
    today_events = CalendarEvent.objects.filter(
        start=date.today()).exclude(title__icontains="born")
    return render(
        request,
        'records/index.html',
        {
            'calendar_config_options': calendar_options(event_url, OPTIONS),
            "today": today,
            "today_events": today_events,
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


class SearchList(View):

    def get(self, request):
        search_term = request.GET.get("search", None)
        print("search: " + search_term)
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
            horses = Horse.objects.filter(
                Q(name__icontains=search_term) |
                Q(notes__icontains=search_term)
            )
            medicines = Medicine.objects.filter(
                Q(name__icontains=search_term) |
                Q(notes__icontains=search_term)
            )
        print(horses)
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
