from django.urls import path
from .views import SearchListView, SearchDetailView


urlpatterns = [
    path('', SearchListView.as_view()),
    path('<pk>', SearchDetailView.as_view()),


]