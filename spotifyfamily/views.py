from django.http import HttpResponse
from django.template import loader

from .models import Subscription

# Create your views here.
def index(request):
    subscriptions = Subscription.objects.order_by("-start_date")
    template = loader.get_template("index.html")
    context = {"subscriptions": subscriptions}
    return HttpResponse(template.render(context, request))
