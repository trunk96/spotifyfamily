from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class Subscription(models.Model):
    start_date = models.DateField()
    name = models.CharField(max_length=100)
    users = models.ManyToManyField("User", through="SubscriptionDetails")
    renew_period = models.IntegerField(default=1)  # in months
    cost = models.FloatField()  # in EUR
    def __str__(self):
        return f"{self.name} - from {self.start_date}"
    
class User(AbstractUser):
    email = models.EmailField('email address', unique=True)
    subscriptions = models.ManyToManyField(Subscription, through="SubscriptionDetails")
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []


class SubscriptionDetails(models.Model):
    last_payment_date = models.DateField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "subscription"], name="unique_user_subscription"
            )
        ]
