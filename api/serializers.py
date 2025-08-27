from rest_framework import serializers
from .models import SparqlEndpoint


class SparqlEndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = SparqlEndpoint
        fields = '__all__'
