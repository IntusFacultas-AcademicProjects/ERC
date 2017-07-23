import datetime
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import View
from django.contrib import messages
from django.db.models import Q

from records.forms import MedicineForm, ScheduleFormSet, \
    TemporaryMedicineForm
from records.models import Medicine, Horse
from records.utils import create_event, delete_event, update_event


class MedicineList(View):

    def get(self, request):
        medicines = Medicine.objects.all()
        medicines = medicines.filter(date_to_start__isnull=True)
        parameters = request.GET.copy()
        parameters = {k: v for k, v in parameters.items() if v}
        keyword = parameters.get("keyword", None)
        frequency = parameters.get("frequency", None)
        doses = parameters.get("doses", None)
        interval = parameters.get("interval", None)
        classification = parameters.get("classification", None)
        if keyword is not None:
            medicines = medicines.filter(
                Q(name__icontains=keyword) |
                Q(notes__icontains=keyword)
            )
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
            update_event(medicine=medicine)
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
                update_event(medicine=medicine)
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
        delete_event(medicine=medicine)
        medicine.delete()
        messages.success(request, "Medicine successfully deleted.")
        return HttpResponseRedirect(reverse_lazy("records:medicine-list"))
    messages.error(request, "Medicine does not exist.")
    return HttpResponseRedirect(reverse_lazy("records:medicine-list"))


def delete_temp_medicine(request, pk, med):
    medicine = Medicine.objects.get(pk=med)
    if medicine:
        delete_event(horse=Horse.objects.get(pk=pk), medicine=medicine)
        medicine.delete()
        messages.success(request, "Medicine successfully deleted.")
        return HttpResponseRedirect(
            reverse_lazy('records:review-horse', kwargs={"pk": pk})
        )
    messages.error(request, "Medicine does not exist.")
    return HttpResponseRedirect(
        reverse_lazy('records:review-horse', kwargs={"pk": pk})
    )


class AddTemporaryMedicine(View):
    """
    Updated temporary medicine that is not based
    on the date the horse is born.
    Template: temporary_medicine_form.html
    """

    def post(self, request, pk, med):
        parameters = request.POST.copy()
        del parameters['csrfmiddlewaretoken']
        horse = Horse.objects.get(pk=pk)
        form = TemporaryMedicineForm(parameters)
        if not form.is_valid():
            return render(
                request,
                'records/temporary_medicine_form.html',
                {
                    "form": form,
                    "horse": horse
                }
            )
        else:
            medicine = Medicine.objects.filter(pk=med)
            medicine.update(**form.cleaned_data)
            messages.success(
                request, "Successfully updated temporary medicine.")
            create_event(horse, medicine)
            return HttpResponseRedirect(
                reverse_lazy('records:review-horse', kwargs={"pk": pk}))

    def get(self, request, pk, med):
        medicine = Medicine.objects.get(pk=pk)
        form = TemporaryMedicineForm(instance=medicine)
        horse = Horse.objects.get(pk=pk)
        return render(
            request,
            'records/temporary_medicine_form.html',
            {
                "form": form,
                "horse": horse
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
            create_event(horse, medicine)
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
