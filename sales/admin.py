from django.contrib import admin
from .models import Order, OrderBump

admin.site.register(Order)
admin.site.register(OrderBump)
