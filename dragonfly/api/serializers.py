from rest_framework import serializers
from dragonfly.models import Search


class SearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Search
        fields = ('origins', 'destinations')
