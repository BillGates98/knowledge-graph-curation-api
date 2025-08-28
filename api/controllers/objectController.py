import asyncio
import django.urls
import multiprocessing
import subprocess
import threading
import time
import os
from api.services.object_services import ObjectService
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from api.models import ComputationStatus, KnowledgeGraph


class ObjectAPIView(APIView):

    def get(self, request, action=None, format=None):
        data = request.GET
        if action == "list-sim":
            min_score = data.get('minScore')
            max_score = data.get('maxScore')
            limit = data.get('limit', -1)
            page = data.get('page', 1)

            objects, total_count, page_count = ObjectService(
                kg_name=data.get("kgName")).fetch_similar_objects(
                min_score=float(min_score) if min_score else 0.0,
                max_score=float(max_score) if max_score else 1.0,
                limit=int(limit),
                page=int(page)
            )
            return Response({"objects": objects, "total_count": total_count, "page_count": page_count}, status=status.HTTP_200_OK)
        elif action == "count-results":
            min_score = data.get('minScore')
            max_score = data.get('maxScore')
            limit = data.get('limit', -1)
            page = data.get('page', 1)

            _, total_count, page_count = ObjectService(
                kg_name=data.get("kgName")).fetch_similar_objects(
                min_score=float(min_score) if min_score else 0.0,
                max_score=float(max_score) if max_score else 1.0,
                limit=int(limit),
                page=int(page)
            )
            return Response({"total_count": total_count, "page_count": page_count}, status=status.HTTP_200_OK)
        elif action == "generate-correspondences":
            min_score = data.get('minScore', 0.5)
            max_score = data.get('maxScore', 1.0)
            limit = data.get('limit', -1)
            page = data.get('page', 1)

            correspondences, correspondence_file_path, query_file_path = ObjectService(
                kg_name=data.get("kgName")).generate_correspondences(
                min_score=float(min_score) if min_score else 0.0,
                max_score=float(max_score) if max_score else 1.0,
                limit=int(limit),
                page=int(page)
            )
            return Response({"correspondences": correspondences, "correspondence_file_name": correspondence_file_path, "query_file_name": query_file_path}, status=status.HTTP_200_OK)
        elif action == "download-file":
            path = data.get('filePath')
            if not path:
                return Response({"error": "File path is required"}, status=status.HTTP_400_BAD_REQUEST)
            if not os.path.exists(path):
                return Response({"error": "File not found"}, status=status.HTTP_404_NOT_FOUND)
            with open(path, 'rb') as f:
                response = HttpResponse(
                    f.read(), content_type="application/octet-stream")
                response[
                    'Content-Disposition'] = f'attachment; filename="{os.path.basename(path)}"'
                return response

        return Response(data, status=status.HTTP_200_OK)

    def post(self, request, action=None, format=None):
        data = request.data
        if action == "fetch":
            objects = ObjectService(
                kg_name=data.get("kgName")).fetch_objects()
            return Response(objects, status=status.HTTP_200_OK)
        elif action == "compute-similarities":
            knowledgeGraph = KnowledgeGraph.objects.filter(
                name=data.get("kgName")).first()
            cs = ComputationStatus.objects.filter(
                knowledgeGraph=knowledgeGraph.id, status="IN_PROGRESS").first()
            if cs:
                return Response({"message": "Computation already in progress"}, status=status.HTTP_200_OK)
            p = threading.Thread(target=ObjectService(
                kg_name=data.get("kgName")).compute_object_similarities, name=f"Object Similarity Computation on Kg: {data.get('kgName')}")
            p.start()
            return Response({"message": "Computation started"}, status=status.HTTP_200_OK)

        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, action=None, format=None):
        data = request.GET
        if action == "delete-sim":
            min_score = data.get('minScore')
            max_score = data.get('maxScore')
            limit = data.get('limit', 100)
            page = data.get('page', 1)

            remaining_count, page_count = ObjectService(
                kg_name=data.get("kgName")).delete_similar_objects(
                min_score=float(min_score) if min_score else 0.0,
                max_score=float(max_score) if max_score else 1.0,
                limit=int(limit),
                page=int(page)
            )
            return Response({"remaining_count": remaining_count, "page_count": page_count-1}, status=status.HTTP_200_OK)
        elif action == "delete":
            data = request.GET
            id = data.get('id')
            if not id:
                return Response({"error": "ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            result = ObjectService(kg_name=None).delete_object(id)
            return Response({"message": "Object deletion", "result": result}, status=status.HTTP_200_OK)
        return Response(data, status=status.HTTP_400_BAD_REQUEST)
