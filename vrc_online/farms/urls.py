
from django.conf.urls import url
from . import views

app_name = "farms"
urlpatterns = [
    url(r'^$', views.FarmList.as_view(), name="farm-list"),
    url(r'^(?P<pk>[0-9]+)/', views.FarmView.as_view(), name="review-farm"),
    url(r'^(?P<pk>[0-9]+)/delete', views.delete_farm,
        name="delete-farm"),
]
