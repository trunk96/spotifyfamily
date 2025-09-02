from django.urls import path
from django.views.generic.base import TemplateView


from . import views
from django.urls import include

urlpatterns = [
    path("", views.index, name="home"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    #path("accounts/", include("django.contrib.auth.urls")),
]