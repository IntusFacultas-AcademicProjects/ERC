from django.db.models import Q
from django.shortcuts import render
from django.views import View
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from farms.models import Farm
from farms.forms import FarmForm
from records.models import Horse


class FarmList(LoginRequiredMixin, View):

    def get(self, request):
        farms = Farm.objects.all()
        form = FarmForm()
        keyword = request.GET.get("keyword", None)
        if keyword:
            farms = farms.filter(Q(name__icontains=keyword) |
                                 Q(address__icontains=keyword))
        return render(request,
                      'farms/farm_list.html',
                      {
                          "farms": farms,
                          "form": form,
                      }
                      )

    def post(self, request):
        parameters = request.POST.copy()
        del parameters['csrfmiddlewaretoken']
        form = FarmForm(parameters)
        if not form.is_valid():
            farms = Farm.objects.all()
            return render(request,
                          'farms/farm_list.html',
                          {
                              "farms": farms,
                              "form": form,
                          }
                          )
        Farm.objects.create(
            user=request.user,
            name=form.cleaned_data.get("name"),
            address=form.cleaned_data.get("address")
        )
        messages.success(request, "Farm sucessfully created.")
        return HttpResponseRedirect(reverse_lazy("farms:farm-list"))


class FarmView(LoginRequiredMixin, View):

    def get(self, request, pk):
        farm = Farm.objects.get(pk=pk)
        farm_horses = Farm.horses.all()
        horses = Horse.objects.all().exclude(id__in=farm_horses)
        form = FarmForm(instance=farm)
        return render(
            request,
            'farms/farm_view.html',
            {
                "form": form,
                "farm_horse": farm_horses,
                "horses": horses,
                "farm": farm,
            }
        )

    def post(self, request, pk):
        farm = Farm.objects.get(pk=pk)
        horses = request.POST.get("horses", None)
        present_horses = farm.horses.all()
        for horse in present_horses:
            if horses.filter(pk=horse.id).count() == 0:
                farm.horses.remove(horse)
        for horse in horses:
            farm.horses.add(horse)
        messages.success(request, "Horses in farm successfully updated.")
        return HttpResponseRedirect(
            reverse_lazy("farms:review-farm", kwargs={"pk": pk})
        )


@login_required
def delete_farm(request, pk):
    farm = Farm.objects.get(pk=pk)
    farm.delete()
    messages.sucess(request, "Farm successfully deleted.")
    return HttpResponseRedirect(reverse_lazy("farms:farm-list"))
