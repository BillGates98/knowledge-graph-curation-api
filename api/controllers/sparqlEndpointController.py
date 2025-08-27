import asyncio
import multiprocessing
import re
import subprocess
import threading
import time
import os
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.http import JsonResponse
from api.services.sparqlendpoint_services import SparqlEndpointService
from api.models import SparqlEndpoint
from api.serializers import SparqlEndpointSerializer

#  http://sparql.southgreen.fr/?default-graph-uri=&query=select+distinct+%3FConcept+where+%7B%5B%5D+a+%3FConcept%7D+LIMIT+100&format=application%2Fsparql-results%2Bjson&timeout=0&debug=on&run=+Run+Query+


class SparqlEndpointAPIView(APIView):

    def get(self, request, action=None, format=None):
        if action == "list-endpoints":
            endpoints = SparqlEndpointService(data=None).get_all_endpoints()
            return Response(endpoints, status=status.HTTP_200_OK)

    def post(self, request, action=None, format=None):
        data = request.data
        if action == "create":
            endpoint = SparqlEndpointService(data=data).create()
            serializer = SparqlEndpointSerializer(endpoint)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, action=None, format=None):
        data = request.data
        id = request.data.get("id")
        if action == "update":
            endpoint = SparqlEndpointService(data=data).update()
            serializer = SparqlEndpointSerializer(endpoint)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"message": "Resource not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, action=None, format=None):
        data = request.GET
        if action == "delete":
            endpoint = SparqlEndpointService(data=data).delete()
            if endpoint:
                return Response({"message": "Resource deleted"}, status=status.HTTP_204_NO_CONTENT)
            return Response({"message": "Resource not found"}, status=status.HTTP_404_NOT_FOUND)
