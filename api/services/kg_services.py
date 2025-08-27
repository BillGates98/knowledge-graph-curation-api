from SPARQLWrapper import SPARQLWrapper, JSON
from api.models import KnowledgeGraph, SparqlEndpoint


class KnowledgeGraphService:

    def __init__(self, data=None):
        self.data = data

    def get_all_graphs(self):
        output = []
        sparqlEndpoint = SparqlEndpoint.objects.filter(
            uri=self.data['sparqlEndpoint']).first()
        if not sparqlEndpoint:
            sparqlEndpoint = SparqlEndpoint(uri=self.data['sparqlEndpoint'])
            sparqlEndpoint.save()
        sparql = SPARQLWrapper(sparqlEndpoint.uri)
        sparql.setQuery("""
            SELECT ?graph WHERE {
                GRAPH ?graph {
                    ?s ?p ?o
                }
            }
        """)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        for result in results["results"]["bindings"]:
            graph_name = result["graph"]["value"]
            check = KnowledgeGraph.objects.filter(
                name=graph_name).exists()
            if not check:
                _kg = KnowledgeGraph(
                    name=graph_name, sparqlEndpointId=sparqlEndpoint)
                _kg.save()
        output = KnowledgeGraph.objects.all().values()
        return output

    def list_kg(self):
        return KnowledgeGraph.objects.all().values()

    def fetch_kg(self):
        results = self.get_all_graphs()
        return results
