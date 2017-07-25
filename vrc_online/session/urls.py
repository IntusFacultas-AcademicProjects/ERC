from django.conf.urls import url
from django.contrib.auth import views as auth_views
from . import views

app_name = "session"
urlpatterns = [
    url(r'^$', views.HomeView.as_view(), name="home"),
    url(r'^signup/$', views.AccountCreation.as_view(), name='signup'),
    url(r'^login/$', auth_views.LoginView.as_view(), name="login"),
    url(r'^logout/$', views.logoutUser, name="logout"),
    url(
        r'^password_reset/$',
        views.password_reset,
        name='password_reset'
    ),
    url(
        r'^password_reset/done/$',
        views.password_reset_done,
        name='password_reset_done'
    ),
    url(
        r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/' +
        '(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        views.password_reset_confirm, name='password_reset_confirm'),
    url(
        r'^reset/done/$',
        views.password_reset_complete,
        name='password_reset_complete'
    ),
    url(
        r'^account_activation_sent/$',
        views.account_activation_sent,
        name='account_activation_sent'
    ),
    url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/' +
        '(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        views.activate, name='activate'),

]
