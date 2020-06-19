
from django.conf.urls import include
from django.contrib import admin
from django.urls import path, re_path
from . import views
#from hello_app import views

app_name = 'dragonfly'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('search', views.search, name='search'),
    path('test', views.test, name='test'),
    path('results', views.results, name='results'),
    path('checkout/<int:pk>', views.checkout, name='checkout'),
    path('create_reservation', views.create_reservation, name='create_reservation'),
    path('reservation_details/<int:pk>', views.reservation_details, name='reservation_details'),
    path('see_itinerary/<int:pk>', views.see_itinerary, name='see_itinerary'),
    path('return_something', views.return_something, name='return_something'),
    path('search_details/<int:pk>/', views.search_details.as_view(), name='search_details'),

    path('get_airports/<str:text>', views.get_airports, name='get_airports'),

    path('conversion', views.conversion, name='conversion'),
    path('populate_cache', views.populate_cache, name='populate_cache'),
    path('user_login', views.user_login, name='user_login'),
    path('user_logout', views.user_logout, name='user_logout'),
    path('user_register', views.user_register, name='user_register'),



]


