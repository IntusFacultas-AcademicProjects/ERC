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
from session.models import Profile


class FarmList(LoginRequiredMixin, View):

    def get(self, request):
        user = request.user
        profile = Profile.objects.get(user__id=user.id)
        farms = Farm.objects.all()
        farms = farms.filter(profile__id=profile.id)
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
        user = request.user
        profile = Profile.objects.get(user__id=user.id)
        parameters = request.POST.copy()
        del parameters['csrfmiddlewaretoken']
        form = FarmForm(parameters)
        if not form.is_valid():
            farms = Farm.objects.all()
            farms = farms.filter(profile__id=profile.id)
            return render(request,
                          'farms/farm_list.html',
                          {
                              "farms": farms,
                              "form": form,
                          }
                          )
        Farm.objects.create(
            name=form.cleaned_data.get("name"),
            address=form.cleaned_data.get("address"),
            profile=profile
        )
        messages.success(request, "Farm sucessfully created.")
        return HttpResponseRedirect(reverse_lazy("farms:farm-list"))


class FarmView(LoginRequiredMixin, View):

    def get(self, request, pk):
        user = request.user
        profile = Profile.objects.get(user__id=user.id)
        farm = Farm.objects.get(pk=pk, profile__id=profile.id)
        farm_horses = farm.horses.all()
        horses = Horse.objects.all().filter(
            profile__id=profile.id).exclude(id__in=farm_horses)
        form = FarmForm(instance=farm)
        return render(
            request,
            'farms/farm_view.html',
            {
                "form": form,
                "farm_horses": farm_horses,
                "horses": horses,
                "farm": farm,
            }
        )

    def post(self, request, pk):
        user = request.user
        profile = Profile.objects.get(user__id=user.id)
        farm = Farm.objects.get(pk=pk, profile__id=profile.id)
        _method = request.POST.get("_method")
        if _method == "ADD_HORSES":
            for horseid in request.POST.get("horses"):
                horse = Horse.objects.get(pk=horseid, profile__id=profile.id)
                farm.horses.add(horse)
            messages.success(request, "Horses successfully added to farm.")
            return HttpResponseRedirect(
                reverse_lazy("farms:review-farm", kwargs={"pk": pk})
            )
        elif _method == "EDIT_FARM":
            parameters = request.POST.copy()
            del parameters["csrfmiddlewaretoken"]
            form = FarmForm(parameters)
            if form.is_valid():
                farm.name = form.cleaned_data.get("name")
                farm.address = form.cleaned_data.get("address")
                farm.profile = profile
                messages.success(request, "Farm successfully updated.")
                return HttpResponseRedirect(
                    reverse_lazy("farms:review-farm", kwargs={"pk": pk})
                )
            farm_horses = farm.horses.all()
            horses = Horse.objects.all().filter(
                profile__id=profile.id).exclude(id__in=farm_horses)
            return render(
                request,
                'farms/farm_view.html',
                {
                    "form": form,
                    "farm_horses": farm_horses,
                    "horses": horses,
                    "farm": farm,
                }
            )
        elif _method == "REMOVE_HORSES":
            for horseid in request.POST.get("horses"):
                horse = Horse.objects.get(pk=horseid, profile__id=profile.id)
                farm.horses.remove(horse)
            messages.success(request, "Horses successfully removed from farm.")
            return HttpResponseRedirect(
                reverse_lazy("farms:review-farm", kwargs={"pk": pk})
            )


@login_required
def delete_farm(request, pk):
    user = request.user
    profile = Profile.objects.get(user__id=user.id)
    farm = Farm.objects.get(pk=pk, profile__id=profile.id)
    farm.delete()
    messages.sucess(request, "Farm successfully deleted.")
    return HttpResponseRedirect(reverse_lazy("farms:farm-list"))
