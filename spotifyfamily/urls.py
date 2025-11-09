from django.urls import path
from django.views.generic.base import TemplateView


from . import views
from django.urls import include

urlpatterns = [
    path("", views.index, name="home"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("subscription/create/", views.create_subscription, name="create_subscription"),
    path("subscription/<int:pk>/edit/", views.edit_subscription, name="edit_subscription"),
    path("subscription/<int:pk>/delete/", views.delete_subscription, name="delete_subscription"),
    path("subscription/<int:subscription_id>/user/<int:user_id>/payment/", views.register_payment, name="register_payment"),
    #path("accounts/", include("django.contrib.auth.urls")),
]