from django.http import HttpResponse
from django.template import loader
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render
from .models import Subscription, SubscriptionDetail, SubscriptionPrice
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import logout
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

# Create your views here.
def index(request):
    subscriptions = Subscription.objects.order_by("-start_date")
    template = loader.get_template("home.html")
    context = {"subscriptions": subscriptions}
    return HttpResponse(template.render(context, request))


@login_required
@require_POST
def create_subscription(request):
    name = request.POST.get("name")
    start_date = request.POST.get("start_date")
    renew_period = request.POST.get("renew_period", 1)
    price = request.POST.get("price")
    if name and start_date and renew_period and price:
        sub = Subscription.objects.create(
            name=name,
            start_date=start_date,
            admin=request.user,
            renew_period=renew_period,
        )
        SubscriptionDetail.objects.create(
            subscription=sub,
            user=request.user,
            last_payment_date=start_date,
        )
        SubscriptionPrice.objects.create(
            subscription=sub,
            price=price,
            valid_from=start_date,
        )
        messages.success(request, "Subscription added successfully.")
        return redirect("home")
    else:
        messages.error(request, "All fields marked with * are required.")
    return render(request, "home.html")


def subscription_detail(request, pk):
    subscription = Subscription.objects.get(pk=pk)
    return render(request, "subscription_detail.html", {"subscription": subscription})

@login_required
def edit_subscription(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk)
    if request.user != subscription.admin:
        messages.error(request, "You are not authorized to edit this subscription.")
        return redirect("home")
    if request.method == "POST":
        name = request.POST.get("name")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date", None)
        if name and start_date and end_date:
            subscription.name = name
            subscription.start_date = start_date
            subscription.end_date = end_date
            subscription.save()
            messages.success(request, "Subscription updated successfully.")
            return redirect("subscription_detail", pk=subscription.pk)
        else:
            messages.error(request, "All fields marked with * are required.")
    return render(request, "edit_subscription.html", {"subscription": subscription})

@login_required
@require_POST
def delete_subscription(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk)
    if request.user != subscription.admin:
        messages.error(request, "You are not authorized to delete this subscription.")
        return redirect("home")
    subscription.delete()
    messages.success(request, "Subscription deleted successfully.")
    return redirect("home")


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