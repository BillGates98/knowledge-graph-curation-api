from django.shortcuts import render

# Create your views here.
from .controllers.knowledgeGraphController import KnowledgeGraphAPIView
from .controllers.subjectController import SubjectAPIView
from .controllers.predicateController import PredicateAPIView
from .controllers.objectController import ObjectAPIView
