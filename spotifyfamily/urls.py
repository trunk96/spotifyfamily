from django.urls import path
from django.views.generic.base import TemplateView

from . import views

urlpatterns = [
    #path("", views.index, name="index"),
    path("", TemplateView.as_view(template_name="home.html"), name="home"),  # new
    path("login/", TemplateView.as_view(template_name="registration/login.html"), name="login"),
]