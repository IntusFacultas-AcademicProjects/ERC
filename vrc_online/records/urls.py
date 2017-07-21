
from django.conf.urls import url
from . import views

app_name = "records"
urlpatterns = [
    url(r'^$', views.index, name="index"),
    url(r'^all_events/$', views.all_events, name='all_events'),
    url(
        r'^medicine/create/$',
        views.CreateMedicine.as_view(),
        name="create-medicine"
    ),
    url(
        r'^medicine/(?P<pk>[0-9]+)/create-schedules/$',
        views.CreateSchedule.as_view(),
        name="add-schedules"
    ),
    url(
        r'^horse/(?P<pk>[0-9]+)/add-medicine/$',
        views.AddMedicine.as_view(),
        name="apply-medicine"
    ),
    url(
        r'^horse/create/$',
        views.CreateHorse.as_view(),
        name="create-horse"
    ),
    url(
        r'^horse/list/$',
        views.HorseList.as_view(),
        name="horse-list"
    ),
    url(
        r'^horse/(?P<pk>[0-9]+)/review/$',
        views.HorseView.as_view(),
        name="review-horse"
    ),
    url(
        r'^horse/(?P<pk>[0-9]+)/delete/$',
        views.delete_horse,
        name="delete-horse"
    ),
    url(
        r'^medicine/(?P<pk>[0-9]+)/delete/$',
        views.delete_medicine,
        name="delete-medicine"
    ),
    url(
        r'^medicine/list/$',
        views.MedicineList.as_view(),
        name="medicine-list"
    ),
    url(
        r'^medicine/(?P<pk>[0-9]+)/review/$',
        views.MedicineView.as_view(),
        name="review-medicine"
    ),
    url(
        r'^search/$',
        views.SearchList.as_view(),
        name="search"
    )
]
