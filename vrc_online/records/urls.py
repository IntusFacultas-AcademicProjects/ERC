
from django.conf.urls import url
from records.views import horse_views, medicine_views, index_views

app_name = "records"
urlpatterns = [
    url(r'^$', index_views.index, name="index"),
    url(r'^all_events/$', index_views.all_events, name='all_events'),
    url(
        r'^medicine/create/$',
        medicine_views.CreateMedicine.as_view(),
        name="create-medicine"
    ),
    url(
        r'^medicine/(?P<pk>[0-9]+)/create-schedules/$',
        medicine_views.CreateSchedule.as_view(),
        name="add-schedules"
    ),
    url(
        r'^horse/(?P<pk>[0-9]+)/add-medicine/$',
        medicine_views.AddMedicine.as_view(),
        name="apply-medicine"
    ),
    url(
        r'^horse/(?P<pk>[0-9]+)/temporary-medicine/(?P<med>[0-9]+)/$',
        medicine_views.AddTemporaryMedicine.as_view(),
        name="edit-temporary-medicine"
    ),
    url(
        r'^horse/create/$',
        horse_views.CreateHorse.as_view(),
        name="create-horse"
    ),
    url(
        r'^horse/list/$',
        horse_views.HorseList.as_view(),
        name="horse-list"
    ),
    url(
        r'^horse/(?P<pk>[0-9]+)/review/$',
        horse_views.HorseView.as_view(),
        name="review-horse"
    ),
    url(
        r'^horse/(?P<pk>[0-9]+)/delete/$',
        horse_views.delete_horse,
        name="delete-horse"
    ),
    url(
        r'^medicine/(?P<pk>[0-9]+)/delete/$',
        medicine_views.delete_medicine,
        name="delete-medicine"
    ),
    url(
        r'^horse/(?P<pk>[0-9]+)/temporary-medicine/(?P<med>[0-9]+)/delete/$',
        medicine_views.delete_temp_medicine,
        name="delete-temp-medicine"
    ),
    url(
        r'^medicine/list/$',
        medicine_views.MedicineList.as_view(),
        name="medicine-list"
    ),
    url(
        r'^medicine/(?P<pk>[0-9]+)/review/$',
        medicine_views.MedicineView.as_view(),
        name="review-medicine"
    ),
    url(
        r'^search/$',
        index_views.SearchList.as_view(),
        name="search"
    )
]
