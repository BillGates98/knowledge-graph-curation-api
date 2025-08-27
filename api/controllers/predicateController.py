import asyncio
import multiprocessing
import subprocess
import threading
import time
import os
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status


class PredicateAPIView(APIView):

    def get(self, request, format=None):
        print(f"GET Request received: {request}")
        for key, value in request.GET.items():
            print(f"Query parameter: {key}, Value: {value}")

        data = [
            {
                'name': 'Knowledge graph curation',
                'description': 'cleansing and enriching knowledge graphs.',
                'date': '2025-08-27'
            }
        ]
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request, action=None, format=None):
        data = request.data
        if action == "save":
            return Response(data, status=status.HTTP_201_CREATED)
        elif action == "stop":
            return Response(data, status=status.HTTP_200_OK)
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, format=None):
        print(f"PUT Request received: {request}")
        data = request.data
        print(f"Data received in PUT: {data}")
        return Response({"message": "Resource updated (PUT)", "data": data}, status=status.HTTP_200_OK)

    def patch(self, request, format=None):
        print(f"PATCH Request received: {request}")
        data = request.data
        print(f"Data received in PATCH: {data}")
        return Response({"message": "Resource partially updated (PATCH)", "data": data}, status=status.HTTP_200_OK)

    def delete(self, request, format=None):
        print(f"DELETE Request received: {request}")
        return Response({"message": "Resource deleted"}, status=status.HTTP_204_NO_CONTENT)

    def options(self, request, format=None):
        print(f"OPTIONS Request received: {request}")
        return Response(status=status.HTTP_200_OK)
