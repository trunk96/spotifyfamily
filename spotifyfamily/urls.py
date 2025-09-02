from django.urls import path
from django.views.generic.base import TemplateView


from . import views
from django.urls import include

urlpatterns = [
    path("", views.index, name="home"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("subscription/create/", views.create_subscription, name="create_subscription"),
    path("subscription/<int:pk>/", views.subscription_detail, name="subscription_detail"),
    #path("accounts/", include("django.contrib.auth.urls")),
]