__author__ = 'SGV'

from django.contrib import admin
from .models import (Itinerary, Passenger, Reservation, Search)


admin.site.register(Search)
admin.site.register(Itinerary)
admin.site.register(Passenger)
admin.site.register(Reservation)

