from django.urls import path, re_path

from api.controllers.sparqlEndpointController import SparqlEndpointAPIView
from .views import KnowledgeGraphAPIView, SubjectAPIView, PredicateAPIView, ObjectAPIView

urlpatterns = [
    #
    path('sparql-endpoints/<str:action>',
         SparqlEndpointAPIView.as_view(), name='sparql-endpoint-api'),
    path('knowledge-graphs/<str:action>',
         KnowledgeGraphAPIView.as_view(), name='kg-api'),
    path('subjects/<str:action>', SubjectAPIView.as_view(), name='subject-api'),
    path('predicates/<str:action>',
         PredicateAPIView.as_view(), name='predicate-api'),
    path('objects/<str:action>', ObjectAPIView.as_view(), name='object-api'),

    #
]
