from django.db import models

# Create your models here.

# SparqlEndpoint model


class SparqlEndpoint(models.Model):
    id = models.AutoField(primary_key=True)
    uri = models.TextField()
    createdAt = models.DateField(auto_now_add=True)

# KnowledgeGraph model


class KnowledgeGraph(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField()
    sparqlEndpointId = models.ForeignKey(
        SparqlEndpoint, on_delete=models.CASCADE)
    createdAt = models.DateField(auto_now_add=True)

# Subject model


class Subject(models.Model):
    id = models.AutoField(primary_key=True)
    knowledgeGraphId = models.ForeignKey(
        KnowledgeGraph, on_delete=models.CASCADE)
    uri = models.TextField()
    createdAt = models.DateField(auto_now_add=True)


class SimSubject(models.Model):
    id = models.AutoField(primary_key=True)
    uri = models.TextField()
    score = models.FloatField()
    subjectId = models.ForeignKey(Subject, on_delete=models.CASCADE)
    createdAt = models.DateField(auto_now_add=True)

# Predicate model


class Predicate(models.Model):
    id = models.AutoField(primary_key=True)
    knowledgeGraphId = models.ForeignKey(
        KnowledgeGraph, on_delete=models.CASCADE)
    uri = models.TextField()
    createdAt = models.DateField(auto_now_add=True)


class SimPredicate(models.Model):
    id = models.AutoField(primary_key=True)
    uri = models.TextField()
    score = models.FloatField()
    predicateId = models.ForeignKey(Predicate, on_delete=models.CASCADE)
    createdAt = models.DateField(auto_now_add=True)

# Object model


class Object(models.Model):
    id = models.AutoField(primary_key=True)
    knowledgeGraphId = models.ForeignKey(
        KnowledgeGraph, on_delete=models.CASCADE)
    uri = models.TextField()
    createdAt = models.DateField(auto_now_add=True)


class SimObject(models.Model):
    id = models.AutoField(primary_key=True)
    uri = models.TextField()
    score = models.FloatField()
    objectId = models.ForeignKey(Object, on_delete=models.CASCADE)
    createdAt = models.DateField(auto_now_add=True)

# computation status


class ComputationStatus(models.Model):
    id = models.AutoField(primary_key=True)
    knowledgeGraph = models.TextField()
    axis = models.TextField()  # subject, predicate, object
    status = models.TextField()  # building_LSH, in_progress, completed
    progress = models.FloatField(default=0.0)
    createdAt = models.DateField(auto_now_add=True)
