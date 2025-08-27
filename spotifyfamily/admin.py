from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Subscription, SubscriptionDetail, SubscriptionPrice

# Register your models here.
admin.site.register(User, UserAdmin)
admin.site.register(Subscription)
admin.site.register(SubscriptionDetail)
admin.site.register(SubscriptionPrice)