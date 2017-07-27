
from django.conf.urls import url
from . import views

app_name = "farms"
urlpatterns = [
    url(r'^$', views.FarmList.as_view(), name="farm-list"),
    url(r'^delete/(?P<pk>[0-9]+)', views.delete_farm,
        name="delete-farm"),
    url(r'^json/(?P<pk>[0-9]+)', views.json_farm, name="json-farm"),
    url(r'^json_all/', views.json_horses, name="json-horses"),
    url(r'^(?P<pk>[0-9]+)/', views.FarmView.as_view(), name="review-farm"),
]
