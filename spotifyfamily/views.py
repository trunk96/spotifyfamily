from django.http import HttpResponse
from django.template import loader
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render
from .models import Subscription
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import logout
from django.views.decorators.http import require_POST

# Create your views here.
def index(request):
    subscriptions = Subscription.objects.order_by("-start_date")
    template = loader.get_template("home.html")
    context = {"subscriptions": subscriptions}
    return HttpResponse(template.render(context, request))


@require_POST
def create_subscription(request):
    name = request.POST.get("name")
    start_date = request.POST.get("start_date")
    end_date = request.POST.get("end_date", None)
    if name and start_date and end_date:
        Subscription.objects.create(
            name=name,
            start_date=start_date,
            end_date=end_date
        )
        messages.success(request, "Subscription added successfully.")
        return redirect("home")
    else:
        messages.error(request, "All fields marked with * are required.")
    return render(request, "home.html")


def subscription_detail(request, pk):
    subscription = Subscription.objects.get(pk=pk)
    return render(request, "subscription_detail.html", {"subscription": subscription})


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
            for _, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
            return render(request, "registration/login.html", {"form": form})
    else:
        form = AuthenticationForm()
        return render(request, "registration/login.html", {"form": form})

def logout_view(request):
    logout(request)
    return redirect("login")