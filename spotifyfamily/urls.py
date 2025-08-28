from django.urls import path
from django.views.generic.base import TemplateView


from . import views
from django.urls import include

urlpatterns = [
    #path("", views.index, name="index"),
    path("", TemplateView.as_view(template_name="home.html"), name="home"),  # new
    path("accounts/", include("django.contrib.auth.urls")),
]