from api.models import SparqlEndpoint


class SparqlEndpointService:

    def __init__(self, data=None):
        self.data = data

    def create(self):
        endpoint = SparqlEndpoint.objects.filter(
            uri=str(self.data.get("sparqlEndpoint"))).first()
        if not endpoint:
            endpoint = SparqlEndpoint(uri=self.data.get("sparqlEndpoint"))
            endpoint.save()
        return endpoint

    def update(self):
        id = self.data.get("id")
        endpoint = SparqlEndpoint.objects.filter(id=id).first()
        if endpoint:
            endpoint.uri = self.data.get("uri", endpoint.uri)
            endpoint.save()
        return endpoint

    def delete(self):
        id = self.data.get("id")
        endpoint = SparqlEndpoint.objects.filter(id=id).first()
        if endpoint:
            endpoint.delete()
            return True
        return False

    def get_all_endpoints(self):
        return SparqlEndpoint.objects.all().values()
