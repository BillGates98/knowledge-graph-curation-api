import asyncio
import multiprocessing
import subprocess
import threading
import time
import os
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from api.services.kg_services import KnowledgeGraphService
from api.models import ComputationStatus

#  http://sparql.southgreen.fr/?default-graph-uri=&query=select+distinct+%3FConcept+where+%7B%5B%5D+a+%3FConcept%7D+LIMIT+100&format=application%2Fsparql-results%2Bjson&timeout=0&debug=on&run=+Run+Query+


class KnowledgeGraphAPIView(APIView):

    def get(self, request, action=None, format=None):
        if action == "list-kgs":
            kgs = KnowledgeGraphService(data=None).list_kg()
            return Response(kgs, status=status.HTTP_200_OK)
        elif action == "computation-status":
            computation_status = ComputationStatus.objects.select_related('knowledgeGraph').all(
            ).values()
            return Response(computation_status, status=status.HTTP_200_OK)

    def post(self, request, action=None, format=None):
        data = request.data
        if action == "fetch-kgs":
            kg_service = KnowledgeGraphService(data=data)
            return Response(kg_service.fetch_kg(), status=status.HTTP_200_OK)

        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, action=None, format=None):
        data = request.data
        if action == "update-computation-status":
            computation_status = ComputationStatus.objects.filter(
                id=data.get("id")).first()
            if computation_status:
                # Update the computation status with the new data
                computation_status.progress = data.get(
                    "progress", computation_status.progress)
                computation_status.status = data.get(
                    "status", computation_status.status)
            computation_status.save()
            return Response(data, status=status.HTTP_200_OK)
        return Response({"message": "Resource not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, format=None):
        print(f"DELETE Request received: {request}")
        return Response({"message": "Resource deleted"}, status=status.HTTP_204_NO_CONTENT)
