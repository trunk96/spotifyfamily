from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class Subscription(models.Model):
    start_date = models.DateField()
    name = models.CharField(max_length=100)
    users = models.ManyToManyField("User", through="SubscriptionDetail")
    admin_user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="admin_subscriptions")
    renew_period = models.IntegerField(default=1)  # in months
    def __str__(self):
        return f"{self.name} - from {self.start_date}"

class SubscriptionPrice(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    price = models.FloatField()  # in EUR
    valid_from = models.DateField()
    valid_to = models.DateField(blank=True, null=True)

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
