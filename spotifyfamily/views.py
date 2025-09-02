from django.http import HttpResponse
from django.template import loader
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render
from .models import Subscription
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import logout

# Create your views here.
def index(request):
    subscriptions = Subscription.objects.order_by("-start_date")
    template = loader.get_template("index.html")
    context = {"subscriptions": subscriptions}
    return HttpResponse(template.render(context, request))


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("home")
            else:
                return render(request, "registration/login.html", {"form": form})
        else:
            messages.error(request, form.errors)
            return render(request, "registration/login.html", {"form": form})
    else:
        form = AuthenticationForm()
        return render(request, "registration/login.html", {"form": form})

def logout_view(request):
    logout(request)
    return redirect("login")