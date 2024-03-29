from dateutil import relativedelta
from calendar import monthrange
import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.views import View
from django.contrib import messages

from records.forms import HorseForm, TemporaryMedicineForm
from records.models import Medicine, Horse
from records.utils import (
    remove_temporary_medicines, update_event,
    delete_event, create_event, create_birth_event, create_temp_event
)
from session.models import Profile
from farms.models import Farm


class SoldHorseList(LoginRequiredMixin, View):

    def get(self, request):
        """
        Filters based on parameters passed through the URL
        """
        message = 'This is where you can review your sold horses. Click ' + \
            '"Review"' + \
            ' on any entry to edit their biological information and ' + \
            ' medical' + \
            ' plans. Click "Delete" on the right to delete that horse.'
        sold_list = True
        horses = Horse.objects.all()
        user = request.user
        profile = Profile.objects.get(user__id=user.id)
        horses = horses.filter(profile__id=profile.id)
        horses = horses.filter(sold=True)
        farms = Farm.objects.all().filter(profile__id=profile.id)
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
        farm = parameters.get("farm", None)
        farmName = None
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
        if farm is not None:
            horses = horses.filter(farm__id=farm)
            farms = farms.exclude(id=farm)
            farmName = Farm.objects.get(id=farm, profile__id=profile.id).name
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
        """
        Age as a year and month number is not a real field in the database.
        It is calculated here based on the number of months which is stored
        in the db
        """
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
                "farm": farm,
                "end": end,
                "age_class": age_class,
                "message": message,
                "sold_list": sold_list,
                "farms": farms,
                "farmName": farmName,
            }
        )


class HorseList(LoginRequiredMixin, View):

    def get(self, request):
        """
        Filters based on parameters passed through the URL
        """
        sold_list = False
        message = 'This is where you can review your horses. Click ' + \
            '"Review"' + \
            ' on any entry to edit their biological information and ' + \
            ' medical' + \
            ' plans. Click "Delete" on the right to delete that horse.'
        horses = Horse.objects.all()
        user = request.user
        profile = Profile.objects.get(user__id=user.id)
        farms = Farm.objects.all().filter(profile__id=profile.id)
        # only get horses for one profile
        horses = horses.filter(profile__id=profile.id)
        horses = horses.filter(sold=False)
        parameters = request.GET.copy()
        parameters = {k: v for k, v in parameters.items() if v}
        keyword = parameters.get("keyword", None)
        weight_lower = parameters.get("weight_lower", None)
        weight_upper = parameters.get("weight_upper", None)
        gender = parameters.get("gender", None)
        pregnant = parameters.get("pregnant", None)
        farm = parameters.get("farm", None)
        upper_age = parameters.get("lower_age", None)
        lower_age = parameters.get("upper_age", None)
        age_class = parameters.get("age_class", None)
        start = parameters.get("start", None)
        farmName = None
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
        if farm is not None:
            horses = horses.filter(farm__id=farm)
            farms = farms.exclude(id=farm)
            farmName = Farm.objects.get(id=farm, profile__id=profile.id).name
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
        """
        Age as a number is not a real field in the database.
        It is calculated here
        """
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
                "farm": farm,
                "age_class": age_class,
                "message": message,
                "sold_list": sold_list,
                "farms": farms,
                "farmName": farmName,
            }
        )


@login_required
def cancel_sell_horse(request, pk):
    user = request.user
    profile = Profile.objects.get(user__id=user.id)
    horse = Horse.objects.get(pk=pk, profile__id=profile.id)
    horse.sold = False
    horse.sale_price = 0
    horse.save()
    print(horse.sold)
    return HttpResponseRedirect(reverse_lazy("records:sold-horse-list"))


@login_required
def sell_horse(request, pk):
    user = request.user
    profile = Profile.objects.get(user__id=user.id)
    horse = Horse.objects.get(pk=pk, profile__id=profile.id)
    horse.sold = True
    horse.sale_price = request.POST.get("price")
    horse.save()
    return HttpResponseRedirect(reverse_lazy("records:horse-list"))


class HorseView(LoginRequiredMixin, View):

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
        user = request.user
        profile = Profile.objects.get(user__id=user.id)
        horse = Horse.objects.get(pk=pk, profile__id=profile.id)
        remove_temporary_medicines(request, horse)
        medicines = horse.medicine_set.all()
        schedules = {}
        """
        add_medicines are all medicines that are not
        already added to the horse and are not temporary.
        """
        add_medicines = Medicine.objects.filter(
            profile__id=profile.id).exclude(id__in=medicines)
        add_medicines = add_medicines.filter(horse__isnull=True)
        for medicine in medicines:
            schedules[medicine.id] = medicine.schedules.all()
        form = HorseForm(instance=horse)
        add_schedules = {}
        for medicine in add_medicines:
            add_schedules[medicine.id] = medicine.schedules.all()
        temporary_medicines = Medicine.objects.filter(
            date_to_start__isnull=False, horse__pk=pk, profile__id=profile.id)
        temp_med_form = TemporaryMedicineForm()
        return render(request,
                      'records/horse_view.html',
                      {
                          "form": form,
                          "horse": horse,
                          "medicines": medicines,
                          "schedules": schedules,
                          "add_medicines": add_medicines,
                          "add_schedules": add_schedules,
                          "temp_meds": temporary_medicines,
                          "temp_med_form": temp_med_form,
                      }
                      )

    def post(self, request, pk):
        """
        Does 1 of 4 things based on hidden input passed with form.
        1: Updates horse values
        2: Updates medicines attached to a horse
        3: Adds Temporary Medicines
        4: Attaches new medicines
        """
        user = request.user
        profile = Profile.objects.get(user__id=user.id)
        horse = Horse.objects.filter(pk=pk, profile__id=profile.id)
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
            today = date.today()
            parameters['age'] = self.monthdelta(date, today)
            form = HorseForm(parameters)
            if not form.is_valid():
                horse = Horse.objects.get(pk=pk, profile__id=profile.id)
                medicines = horse.medicine_set.all()
                schedules = {}
                add_medicines = Medicine.objects.filter(
                    profile__id=profile.id).exclude(id__in=medicines)
                add_medicines = add_medicines.filter(horse__isnull=True)
                for medicine in medicines:
                    schedules[medicine.id] = medicine.schedules.all()
                add_schedules = {}
                for medicine in add_medicines:
                    add_schedules[medicine.id] = medicine.schedules.all()
                temporary_medicines = Medicine.objects.filter(
                    date_to_start__isnull=False, horse__pk=pk,
                    profile__id=profile.id)
                temp_med_form = TemporaryMedicineForm()
                return render(request,
                              'records/horse_view.html',
                              {
                                  "form": form,
                                  "horse": horse,
                                  "medicines": medicines,
                                  "schedules": schedules,
                                  "add_medicines": add_medicines,
                                  "add_schedules": add_schedules,
                                  "temp_meds": temporary_medicines,
                                  "temp_med_form": temp_med_form,
                              }
                              )
            parameters["dob"] = self.dob_convert(parameters["dob"])
            horse.update(dob=parameters.get("dob"))
            horse.update(age=parameters.get("age"))
            horse.update(weight=parameters.get("weight"))
            horse.update(name=parameters.get("name"))
            horse.update(notes=parameters.get("notes"))
            horse.update(gender=parameters.get("gender"))
            horse.update(pregnant=parameters.get("pregnant"))
            datest = None
            if parameters.get("date_of_impregnation", None) is not None and \
                    parameters.get("date_of_impregnation", None) != "":
                datest = datetime.datetime.strptime(
                    parameters.get("date_of_impregnation"), "%m/%d/%Y")
            horse.update(date_of_impregnation=datest)
            messages.success(request, "Horse successfully updated.")
            horse = Horse.objects.get(pk=pk)
            horse.refresh_from_db()
            update_event(request, horse=horse)
            return HttpResponseRedirect(
                reverse_lazy('records:review-horse', kwargs={"pk": pk})
            )
        elif parameters.get("_method") == "DELETE_MEDICINE":
            del parameters['_method']
            horse = Horse.objects.get(pk=pk, profile__id=profile.id)
            for key, value in parameters.items():
                medicine = Medicine.objects.get(pk=int(key),
                                                profile__id=profile.id)
                delete_event(request, horse=horse, medicine=medicine)
                medicine.horses.remove(horse)
            messages.success(request, "Medicine successfully removed.")
            return HttpResponseRedirect(
                reverse_lazy('records:review-horse', kwargs={"pk": pk})
            )
        elif parameters.get("_method") == "ADD_MEDICINE":
            del parameters['_method']
            horse = Horse.objects.get(pk=pk)
            for key, value in parameters.items():
                medicine = Medicine.objects.get(pk=int(key),
                                                profile__id=profile.id)
                create_event(request, horse=horse, medicine=medicine)
                medicine.horses.add(horse)
            messages.success(request, "Medicine successfully added.")
            return HttpResponseRedirect(
                reverse_lazy('records:review-horse', kwargs={"pk": pk})
            )
        elif parameters.get("_method") == "EDIT_TEMPS":
            del parameters['_method']
            horse = Horse.objects.get(pk=pk, profile__id=profile.id)
            temp_med_form = TemporaryMedicineForm(parameters)
            if temp_med_form.is_valid():
                temp_med_form.cleaned_data["horse"] = horse
                medicine = Medicine.objects.create(
                    **temp_med_form.cleaned_data)
                medicine.horse = horse
                medicine.save()
                create_temp_event(request,horse=horse, medicine=medicine)
                messages.success(
                    request,
                    "Temporary medicine successfully added."
                )
                return HttpResponseRedirect(
                    reverse_lazy('records:review-horse', kwargs={"pk": pk})
                )
            else:
                horse = Horse.objects.get(pk=pk, profile__id=profile.id)
                medicines = horse.medicine_set.all()
                schedules = {}
                add_medicines = Medicine.objects.filter(
                    profile__id=profile.id).exclude(id__in=medicines)
                add_medicines = add_medicines.filter(horse__isnull=True)
                for medicine in medicines:
                    schedules[medicine.id] = medicine.schedules.all()
                form = HorseForm(instance=horse)
                add_schedules = {}
                for medicine in add_medicines:
                    add_schedules[medicine.id] = medicine.schedules.all()
                temporary_medicines = Medicine.objects.filter(
                    date_to_start__isnull=False, horse__pk=pk,
                    profile__id=profile.id)
                messages.error(request, "Temporary medicine creation failed.")
                return render(request,
                              'records/horse_view.html',
                              {
                                  "form": form,
                                  "horse": horse,
                                  "medicines": medicines,
                                  "schedules": schedules,
                                  "add_medicines": add_medicines,
                                  "add_schedules": add_schedules,
                                  "temp_meds": temporary_medicines,
                                  "temp_med_form": temp_med_form,
                              }
                              )


class CreateHorse(LoginRequiredMixin, View):
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
        user = request.user
        profile = Profile.objects.get(user__id=user.id)
        parameters = request.POST.copy()
        dob = parameters.get("dob", 0)
        year = dob[6:]
        month = dob[0:2]
        day = dob[3:5]
        date = datetime.date(int(year), int(month), int(day))
        today = date.today()
        del parameters["csrfmiddlewaretoken"]
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
        horse.profile = profile
        horse.save()
        messages.success(request, "Horse successfully created.")
        create_birth_event(request, horse, horse.dob)
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


@login_required
def delete_horse(request, pk):
    user = request.user
    profile = Profile.objects.get(user__id=user.id)
    horse = Horse.objects.get(pk=pk, profile__id=profile.id)
    if horse:
        delete_event(request, horse=horse, delete=True)
        horse.delete()
        messages.success(request, "Horse successfully deleted.")
        return HttpResponseRedirect(reverse_lazy("records:horse-list"))
    messages.error(request, "Horse does not exist.")
    return HttpResponseRedirect(reverse_lazy("records:horse-list"))
