__author__ = 'SGV'

import datetime
from django.db import models
from django.forms.models import model_to_dict


class Search(models.Model):
    origins = models.CharField(max_length=50, blank=True)
    destinations = models.CharField(max_length=50, blank=True)
    dates = models.CharField(max_length=50, blank=True)
    adt = models.IntegerField(default=1, blank=True)
    cnn = models.IntegerField(default=0, blank=True)
    inf = models.IntegerField(default=0, blank=True)
    options_in_cache = models.IntegerField(blank=True, default=0)
    observations = models.CharField(max_length=250, blank=True)
    created = models.DateTimeField(blank=True, null=True)
    updated = models.DateTimeField(blank=True, null=True)
    hits = models.IntegerField(blank=True, null=True, default=0)
    cheapest_price = models.FloatField(default=999999)
    quickest_time = models.PositiveIntegerField(default=0)

    def save_results(self, results) -> None:
        try:
            self.save()
            for itinerar_key, itinerary_details in results.items():
                itin = Itinerary(search_id=self)
                itin.create_(itinerary_details)
                itin.save()

            itineraries = Itinerary.objects.filter(search_id=self.pk)

            self.cheapest_price = min([itin.total_price for itin in itineraries])
            self.quickest_time = min([itin.travel_time for itin in itineraries])

            if self.created is None:
                self.created = datetime.datetime.now()
            self.updated = datetime.datetime.now()

            self.save()
        except Exception as e:
            raise Exception(f'Error trying to save results: {str(e)}')

    def pull(self, sort_criteria='total_price') -> dict:
        try:
            self.hits += 1
            self.save()
            return self.get_json(sort_criteria=sort_criteria)
        except Exception as e:
            raise Exception(f'Error trying to Pull: {str(e)}')

    def get_json(self, sort_criteria='total_price'):
        itineraries = Itinerary.objects.filter(search_id=self.pk).order_by(sort_criteria, 'total_price', 'travel_time')
        return {id: itinerary.get_json() for id, itinerary in enumerate(itineraries)}


class Itinerary(models.Model):
    search_id = models.ForeignKey(Search, on_delete=models.CASCADE)
    main_carrier = models.CharField(max_length=2, blank=True)
    flight_numbers = models.CharField(max_length=200, blank=True)

    departure_airports = models.CharField(max_length=3, blank=True, default='SGV')
    arrival_airports = models.CharField(max_length=3, blank=True, default='SGV')
    departure_times = models.CharField(max_length=5, blank=True, default='12:00')
    arrival_times = models.CharField(max_length=5, blank=True, default='12:00')
    departure_dates = models.CharField(max_length=100, blank=True, default='31-MAR-2021')
    arrival_dates = models.CharField(max_length=100, blank=True, default='31-MAR-2021')
    carriers = models.CharField(max_length=2, blank=True, default='YY')
    rbds = models.CharField(max_length=50, blank=True, default='na')
    cabins = models.CharField(max_length=50, blank=True, default='na')
    bags = models.CharField(max_length=50, blank=True, default='na')

    itinerary_origin = models.CharField(max_length=3, blank=True)
    itinerary_destination = models.CharField(max_length=3, blank=True)
    itinerary_departure_time = models.CharField(max_length=5, blank=True)
    itinerary_arrival_time = models.CharField(max_length=5, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    total_price = models.FloatField(default=0.0)
    travel_time = models.PositiveIntegerField(default=0)
    passenger_count = models.PositiveIntegerField(default=0)
    seat_count = models.PositiveIntegerField(default=0)
    flight_count = models.CharField(max_length=50, default='2,2')


    def create_(self, itinerary):
        def parse_flight_number(f_num: int) -> str:
            """ returns a string 4 in length for flight number passed """
            return (4 - len(str(f_num))) * '0' + str(f_num)

        try:

            self.main_carrier = itinerary['main_carrier']
            self.itinerary_origin = itinerary['itinerary_origin']
            self.itinerary_destination = itinerary['itinerary_destination']
            self.itinerary_departure_time = itinerary['itinerary_departure_time']
            self.currency = itinerary['currency']
            self.total_price = itinerary['total_price']
            self.travel_time = itinerary['travel_time']
            self.passenger_count = itinerary['passenger_count']
            self.seat_count = itinerary['seat_count']

            sep = '|'

            self.bags = sep.join([str(b) for b in itinerary['bags']])
            self.flight_numbers = sep.join(f['carrier'] + parse_flight_number(f['flight_number'])
                                             for f in itinerary['flights'])
            self.departure_airports = sep.join([f['departure_airport'] for f in itinerary['flights']])
            self.arrival_airports = sep.join([f['arrival_airport'] for f in itinerary['flights']])
            self.departure_times = sep.join([f['departure_time'] for f in itinerary['flights']])
            self.arrival_times = sep.join([f['arrival_time'] for f in itinerary['flights']])

            self.departure_dates = sep.join([f['departure_date'] for f in itinerary['flights']])
            self.arrival_dates = sep.join([f['arrival_date'] for f in itinerary['flights']])

            self.carriers = sep.join([f['carrier'] for f in itinerary['flights']])
            self.rbds = sep.join([f['rbd'] for f in itinerary['flights']])
            self.cabins = sep.join([f['cabin'] for f in itinerary['flights']])
            self.flight_count = sep.join([str(f) for f in itinerary['flight_count']])


            self.save()
        except Exception as e:
            raise Exception(f'Error trying to Create Itinerary: {str(e)}')

    def get_json(self) -> dict:
        try:
            sep = '|'
            d = model_to_dict(self, fields=[field.name for field in self._meta.fields])

            flight_count = len(self.flight_numbers.split(sep))

            d['bags'] = min([int(bag) for bag in self.bags.split(sep)])

            d['flights'] = [{'departure_airport': self.departure_airports.split(sep)[i],
                             'arrival_airport': self.arrival_airports.split(sep)[i],
                             'departure_time': self.departure_times.split(sep)[i],
                             'arrival_time': self.arrival_times.split(sep)[i],
                             'departure_date': self.departure_dates.split(sep)[i],
                             'arrival_date': self.arrival_dates.split(sep)[i],
                             'carrier': self.carriers.split(sep)[i],
                             'flight_number': self.flight_numbers.split(sep)[i],

                             }
                            for i in range(flight_count)
                            ]

            d['flight_count'] = [int(fc) for fc in self.flight_count.split(sep)]

            leg_summary = []
            p = 0
            for flight_count in d['flight_count']:
                leg = {
                    'departure_airport': d['flights'][p]['departure_airport'],
                    'departure_time': d['flights'][p]['departure_time'],
                    'departure_date': d['flights'][p]['departure_date'],

                    'arrival_airport': d['flights'][p + flight_count - 1]['arrival_airport'],
                    'arrival_time': d['flights'][p +flight_count - 1]['arrival_time'],
                    'arrival_date': d['flights'][p +flight_count - 1]['arrival_date'],
                 }
                p += flight_count
                leg_summary.append(leg)

            d['leg_summary'] = leg_summary

            return d
        except Exception as e:
            raise Exception(f'Error trying to get Json: {str(e)}')


class Reservation(models.Model):
    itinerary_id = models.ForeignKey(Itinerary, on_delete=models.PROTECT, null=True)

    def get_passengers(self):
        Passenger.objects.filter(reservation_id=self.pk)

    def add_passenger(self, passenger):
        passenger.reservation_id = self
        passenger.save()

    def get_passengers(self):
        return Passenger.objects.filter(reservation_id=self)

    def get_absolute_url(self):
        return f"reservation_details/{str(self.pk)}"


    def get_ond(self):
        return (self.itinerary_id.itinerary_origin+"-"+self.itinerary_id.itinerary_destination)


class Passenger(models.Model):
    name = models.CharField(max_length=200)
    surname = models.CharField(max_length=200)
    phone = models.CharField(max_length=200)
    ptc = models.CharField(max_length=3, default='ADT') #TODO
    profile_id = models.CharField(max_length=2, default='0') #TODO
    reservation_id = models.ForeignKey(Reservation, on_delete=models.PROTECT, null=True)

    def add_to_reservation(self, reservation):
        self.reservation_id = reservation
        self.save()