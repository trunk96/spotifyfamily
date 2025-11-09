from django.db import models
from django.db.models import Q
from django.contrib.auth.models import AbstractUser
from dateutil.relativedelta import relativedelta
from datetime import date

# Create your models here.
class Subscription(models.Model):
    start_date = models.DateField()
    name = models.CharField(max_length=100)
    users = models.ManyToManyField("User", through="SubscriptionDetail")
    admin_user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="admin_subscriptions")
    renew_period = models.IntegerField(default=1)  # in months
    
    def __str__(self):
        return f"{self.name} - from {self.start_date}"
    
    def get_current_price(self):
        """Ritorna il prezzo corrente attivo"""
        return self.prices.filter(valid_to__isnull=True).first()
    
    def get_price_per_user(self):
        """Calcola il prezzo per utente dividendo il prezzo totale per il numero di utenti"""
        current_price = self.get_current_price()
        if not current_price:
            return 0
        user_count = self.users.count()
        if user_count == 0:
            return current_price.price
        return round(current_price.price / user_count, 2)

class SubscriptionPrice(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name="prices")
    price = models.FloatField()  # in EUR
    valid_from = models.DateField()
    valid_to = models.DateField(blank=True, null=True)
    
    def get_price_per_user(self, user_count):
        """Calcola il prezzo per utente per questo prezzo specifico"""
        if user_count == 0:
            return self.price
        return round(self.price / user_count, 2)

class User(AbstractUser):
    subscriptions = models.ManyToManyField(Subscription, through="SubscriptionDetail")

class SubscriptionDetail(models.Model):
    last_payment_date = models.DateField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "subscription"], name="unique_user_subscription"
            )
        ]
    
    def get_last_paid_month(self):
        """Ritorna l'ultimo mese pagato in formato leggibile"""
        return self.last_payment_date.strftime("%B %Y")
    
    def get_months_unpaid(self):
        """Calcola quanti periodi di rinnovo sono passati dall'ultimo pagamento"""
        today = date.today()
        next_payment_date = self.last_payment_date + relativedelta(months=self.subscription.renew_period)
        
        months_count = 0
        while next_payment_date <= today:
            months_count += 1
            next_payment_date += relativedelta(months=self.subscription.renew_period)
        
        return months_count
    
    def get_amount_to_pay(self):
        """
        Calcola l'importo totale da pagare considerando lo storico dei prezzi.
        Per ogni periodo non pagato, usa il prezzo valido in quel periodo.
        """
        today = date.today()
        next_payment_date = self.last_payment_date + relativedelta(months=self.subscription.renew_period)
        
        total_amount = 0.0
        user_count = self.subscription.users.count()
        
        # Per ogni periodo non pagato
        while next_payment_date <= today:
            # Trova il prezzo valido per questo periodo
            # Il prezzo è valido se valid_from <= periodo e (valid_to è null o valid_to >= periodo)
            period_start = next_payment_date - relativedelta(months=self.subscription.renew_period)
            
            price_obj = self.subscription.prices.filter(
                valid_from__lte=next_payment_date
            ).filter(
                models.Q(valid_to__isnull=True) | models.Q(valid_to__gte=period_start)
            ).order_by('-valid_from').first()
            
            if price_obj:
                period_price = price_obj.get_price_per_user(user_count)
                total_amount += period_price
            
            next_payment_date += relativedelta(months=self.subscription.renew_period)
        
        return round(total_amount, 2)
    
    def is_payment_overdue(self):
        """Verifica se ci sono pagamenti non effettuati"""
        return self.get_months_unpaid() > 0

class Payment(models.Model):
    """Modello per tracciare i pagamenti effettuati dagli utenti"""
    subscription_detail = models.ForeignKey(SubscriptionDetail, on_delete=models.CASCADE, related_name="payments")
    amount = models.FloatField()  # Importo pagato in EUR
    payment_date = models.DateField()  # Data del pagamento
    created_at = models.DateTimeField(auto_now_add=True)  # Quando è stato registrato
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.subscription_detail.user.username} - €{self.amount} - {self.payment_date}"
