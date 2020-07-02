from rest_framework.generics import ListAPIView, RetrieveAPIView
from dragonfly.models import Search
from .serializers import SearchSerializer



class SearchListView(ListAPIView):
    queryset = Search.objects.all()
    serializer_class = SearchSerializer


class SearchDetailView(RetrieveAPIView):
    queryset = Search.objects.all()
    serializer_class = SearchSerializer

