from django.http import HttpResponse
from django.template import loader
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render
from .models import Subscription, SubscriptionDetail, SubscriptionPrice, User, Payment
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import logout
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from dateutil.relativedelta import relativedelta
from datetime import date
from django.db.models import Q, Prefetch

# Create your views here.
def calculate_amount_to_pay(detail, user_count, prices_cache):
    """
    Calcola l'importo totale da pagare considerando lo storico dei prezzi.
    Versione ottimizzata con cache dei prezzi.
    """
    today = date.today()
    next_payment_date = detail.last_payment_date + relativedelta(months=detail.subscription.renew_period)
    
    total_amount = 0.0
    
    # Per ogni periodo non pagato
    while next_payment_date <= today:
        period_start = next_payment_date - relativedelta(months=detail.subscription.renew_period)
        
        # Trova il prezzo valido per questo periodo dalla cache
        period_price = None
        for price_obj in prices_cache:
            if price_obj.valid_from <= next_payment_date:
                if price_obj.valid_to is None or price_obj.valid_to >= period_start:
                    period_price = price_obj
                    break
        
        if period_price:
            price_per_user = round(period_price.price / user_count, 2) if user_count > 0 else period_price.price
            total_amount += price_per_user
        
        next_payment_date += relativedelta(months=detail.subscription.renew_period)
    
    return round(total_amount, 2)

def index(request):
    # Usa prefetch_related per ottimizzare le query
    subscriptions = Subscription.objects.prefetch_related(
        Prefetch('prices', queryset=SubscriptionPrice.objects.order_by('-valid_from')),
        Prefetch('users'),
        'admin_user'
    ).order_by("-start_date")
    
    # Prepara i dati con le informazioni di pagamento
    subscriptions_with_payment = []
    for subscription in subscriptions:
        # Cache dei prezzi per questa subscription (già ordinati)
        prices_cache = list(subscription.prices.all())
        user_count = subscription.users.count()
        
        payment_info = {
            'subscription': subscription,
            'user_payments': []
        }
        
        # Ottieni i dettagli di pagamento per ogni utente
        details = SubscriptionDetail.objects.filter(subscription=subscription).select_related('user')
        for detail in details:
            today = date.today()
            next_payment_date = detail.last_payment_date + relativedelta(months=subscription.renew_period)
            
            # Calcola periodi non pagati
            months_count = 0
            temp_date = next_payment_date
            while temp_date <= today:
                months_count += 1
                temp_date += relativedelta(months=subscription.renew_period)
            
            payment_info['user_payments'].append({
                'user': detail.user,
                'last_paid_month': detail.last_payment_date.strftime("%B %Y"),
                'amount_to_pay': calculate_amount_to_pay(detail, user_count, prices_cache),
                'months_unpaid': months_count,
                'is_overdue': months_count > 0
            })
        
        subscriptions_with_payment.append(payment_info)
    
    template = loader.get_template("home.html")
    context = {"subscriptions_data": subscriptions_with_payment}
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
            admin_user=request.user,
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

@login_required
def edit_subscription(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk)
    if request.user != subscription.admin_user:
        messages.error(request, "You are not authorized to edit this subscription.")
        return redirect("home")
    if request.method == "POST":
        action = request.POST.get("action")
        
        if action == "update_subscription":
            name = request.POST.get("name")
            start_date = request.POST.get("start_date")
            renew_period = request.POST.get("renew_period")
            if name and start_date and renew_period:
                subscription.name = name
                subscription.start_date = start_date
                subscription.renew_period = renew_period
                subscription.save()
                messages.success(request, "Subscription updated successfully.")
            else:
                messages.error(request, "All fields are required.")
        
        elif action == "add_price":
            price = request.POST.get("new_price")
            valid_from = request.POST.get("price_valid_from")
            if price and valid_from:
                # Chiudi il prezzo corrente se esiste
                current_prices = subscription.prices.filter(valid_to__isnull=True)
                for current_price in current_prices:
                    current_price.valid_to = valid_from
                    current_price.save()
                
                # Crea il nuovo prezzo
                SubscriptionPrice.objects.create(
                    subscription=subscription,
                    price=price,
                    valid_from=valid_from,
                )
                messages.success(request, "New price added successfully.")
            else:
                messages.error(request, "Price and valid from date are required.")
        
        elif action == "update_current_price":
            price_id = request.POST.get("price_id")
            new_price_value = request.POST.get("current_price")
            if price_id and new_price_value:
                price_obj = get_object_or_404(SubscriptionPrice, pk=price_id)
                price_obj.price = new_price_value
                price_obj.save()
                messages.success(request, "Price updated successfully.")
            else:
                messages.error(request, "Price value is required.")
        
        elif action == "remove_user":
            user_id = request.POST.get("user_id")
            if user_id:
                try:
                    user_to_remove = get_object_or_404(User, pk=user_id)
                    if user_to_remove.id == subscription.admin_user.id:
                        messages.error(request, "Cannot remove the administrator from the subscription.")
                    else:
                        # Rimuovi l'utente tramite SubscriptionDetail
                        SubscriptionDetail.objects.filter(
                            subscription=subscription,
                            user=user_to_remove
                        ).delete()
                        messages.success(request, f"User {user_to_remove.username} removed successfully.")
                except Exception as e:
                    messages.error(request, f"Error removing user: {str(e)}")
            else:
                messages.error(request, "User ID is required.")
        
        return redirect("edit_subscription", pk=pk)
    
    # GET request
    all_users = User.objects.exclude(id=subscription.admin_user.id)
    subscription_users = subscription.users.all()
    current_price = subscription.prices.filter(valid_to__isnull=True).first()
    price_history = subscription.prices.exclude(valid_to__isnull=True).order_by('-valid_from')
    
    context = {
        "subscription": subscription,
        "all_users": all_users,
        "subscription_users": subscription_users,
        "current_price": current_price,
        "price_history": price_history,
    }
    return render(request, "edit_subscription.html", context)

@login_required
@require_POST
def delete_subscription(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk)
    if request.user != subscription.admin_user:
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

@login_required
@require_POST
def register_payment(request, subscription_id, user_id):
    """Registra un pagamento per un utente in una subscription"""
    subscription = get_object_or_404(Subscription, pk=subscription_id)
    
    # Verifica che sia l'amministratore
    if request.user != subscription.admin_user:
        messages.error(request, "Solo l'amministratore può registrare i pagamenti.")
        return redirect("home")
    
    user_to_update = get_object_or_404(User, pk=user_id)
    amount_paid = request.POST.get("amount_paid")
    payment_date = request.POST.get("payment_date")
    
    if not amount_paid or not payment_date:
        messages.error(request, "Importo e data sono richiesti.")
        return redirect("home")
    
    try:
        amount_paid = float(amount_paid)
        
        # Trova il SubscriptionDetail
        detail = SubscriptionDetail.objects.get(subscription=subscription, user=user_to_update)
        
        # Crea il record del pagamento
        Payment.objects.create(
            subscription_detail=detail,
            amount=amount_paid,
            payment_date=payment_date
        )
        
        # Aggiorna la data dell'ultimo pagamento
        detail.last_payment_date = payment_date
        detail.save()
        
        messages.success(request, f"Pagamento di €{amount_paid} registrato per {user_to_update.username}.")
    except SubscriptionDetail.DoesNotExist:
        messages.error(request, "Dettaglio sottoscrizione non trovato.")
    except ValueError:
        messages.error(request, "Importo non valido.")
    except Exception as e:
        messages.error(request, f"Errore nella registrazione del pagamento: {str(e)}")
    
    return redirect("home")