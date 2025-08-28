import json
from SPARQLWrapper import SPARQLWrapper, JSON
from api.models import ComputationStatus, KnowledgeGraph, SimObject, Object
from api.services.lsh_services import LSHService


class ObjectService:

    def __init__(self, kg_name=None):
        self.kg_name = kg_name
        print(f"Initializing ObjectService for KG: {kg_name}")
        self.kg_model = KnowledgeGraph.objects.filter(
            name=kg_name).select_related('sparqlEndpointId').first()

    def get_offset_and_limit(self, page, limit, results_queryset):
        if limit < 0:
            offset = 0
            limit = len(results_queryset)
        else:
            offset = (page - 1) * limit
        return offset, limit

    def get_all_objects(self):
        output = []
        kg_model = self.kg_model
        sparql = SPARQLWrapper(kg_model.sparqlEndpointId.uri)
        sparql.setQuery(f"""
            SELECT ?object WHERE {{
                GRAPH <{kg_model.name}> {{
                    ?subject ?predicate ?object
                }}
            }}
        """)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        for result in results["results"]["bindings"]:
            object_name = result["object"]["value"]
            check = Object.objects.filter(
                uri=object_name, knowledgeGraphId=self.kg_model.id).exists()
            if not check:
                _object = Object(
                    uri=object_name, knowledgeGraphId=self.kg_model)
                _object.save()
        output = Object.objects.filter(
            knowledgeGraphId=self.kg_model).values()
        print(f"Fetched {len(output)} objects for KG: {self.kg_name}")
        return output

    def compute_object_similarities(self):
        objects = Object.objects.filter(
            knowledgeGraphId=self.kg_model.id).values()
        if not objects or len(objects) == 0:
            print(f"No objects found for KG: {self.kg_name}")
            objects = self.get_all_objects()

        print(f"Fetched {len(objects)} objects for KG: {self.kg_name}")
        corpus = [result['uri'] for result in objects]
        computationStatus = ComputationStatus.objects.filter(
            knowledgeGraph=self.kg_model.id, axis='object').first()

        if not computationStatus:
            computationStatus = ComputationStatus(
                knowledgeGraph=self.kg_model.id, axis='object', status='BLSHING')
            computationStatus.save()
        # Simulate computation delay
        print(f"Total corpus : {len(corpus)}")
        lshService = LSHService(corpus=corpus)
        computationStatus.status = 'IN_PROGRESS'
        computationStatus.save()
        for result in lshService.run():
            # save to SimObject
            if result['source'] != result['target']:
                check = SimObject.objects.filter(
                    objectId__uri=result['source'], uri=result['target'], objectId__knowledgeGraphId=self.kg_model.id).exists()
                if not check:
                    _source = Object.objects.filter(
                        uri=result['source'], knowledgeGraphId=self.kg_model.id).first()
                    _target = Object.objects.filter(
                        uri=result['target'], knowledgeGraphId=self.kg_model.id).first()
                    _object = SimObject(
                        objectId=_source, uri=_target.uri, score=result['sim_score'])
                    _object.save()
            # Update progress
            computationStatus.progress += (1.0 / (len(corpus)**2)) * 100
            computationStatus.save()

        computationStatus.status = 'COMPLETED'
        computationStatus.save()
        return computationStatus

    def fetch_objects(self):
        results = self.get_all_objects()
        return results

    def fetch_similar_objects(self, min_score=0.0, max_score=1.0, limit=100, page=1):
        results_queryset = SimObject.objects.filter(
            score__gte=min_score,
            score__lte=max_score,
            objectId__knowledgeGraphId=self.kg_model.id
        ).order_by('-score').select_related('objectId')  # .values()
        page_count = (len(results_queryset) + limit -
                      1) // limit if limit > 0 else 1
        page = max(1, min(page, page_count))  # Ensure page is within bounds
        offset, limit = self.get_offset_and_limit(
            page, limit, results_queryset)
        final_results = []
        for sim_object in results_queryset[offset:offset + limit]:
            final_results.append({
                "sim_object_id": sim_object.id,
                "sim_object_uri": sim_object.uri,
                "object_uri": sim_object.objectId.uri,
                "object_id": sim_object.objectId.id,
                "score": sim_object.score
            })
        return final_results, len(results_queryset), page_count

    def generate_correspondences(self, min_score=0.0, max_score=1.0, limit=100, page=1):
        correspondences = []
        queries = []
        correspondence_file_path = f"/tmp/object_correspondences_kg_{self.kg_model.id}_m_{min_score}_M_{max_score}_l_{limit}_p_{page}.json"
        query_file_path = f"/tmp/object_update_queries_kg_{self.kg_model.id}_m_{min_score}_M_{max_score}_l_{limit}_p_{page}.sparql"
        results, _, _ = self.fetch_similar_objects(
            min_score=min_score,
            max_score=max_score,
            limit=limit,
            page=page
        )
        for result in results:
            correspondences.append(result)
            queries.append(self.update_query(alignment=result))

        with open(correspondence_file_path, 'w') as f:
            json.dump(correspondences, f)

        with open(query_file_path, 'w') as f:
            f.writelines(queries)

        return correspondences, correspondence_file_path, query_file_path

    def update_query(self, alignment=None):
        template = "\nDELETE { ?s ?p %s . }\nINSERT { ?s ?p %s . }\nWHERE  { ?s ?p %s . };\n"
        if alignment:
            if alignment['object_uri'].startswith('http'):
                alignment['object_uri'] = f"<{alignment['object_uri']}>"
            else:
                alignment['object_uri'] = f"\"{alignment['object_uri']}\""

            if alignment['sim_object_uri'].startswith('http'):
                alignment['sim_object_uri'] = f"<{alignment['sim_object_uri']}>"
            else:
                alignment['sim_object_uri'] = f"\"{alignment['sim_object_uri']}\""

            return template % (alignment['object_uri'], alignment['sim_object_uri'], alignment['object_uri'])
        return None

    def delete_similar_objects(self, min_score=0.0, max_score=1.0, limit=100, page=1):
        results_queryset = SimObject.objects.filter(
            score__gte=min_score,
            score__lte=max_score,
            objectId__knowledgeGraphId=self.kg_model.id
        ).select_related('objectId')
        page_count = (len(results_queryset) + limit -
                      1) // limit if limit > 0 else 1
        page = max(1, min(page, page_count))  # Ensure page is within bounds
        offset, limit = self.get_offset_and_limit(
            page, limit, results_queryset)
        ids_to_delete = []
        for sim_object in results_queryset[offset:offset + limit]:
            ids_to_delete.append(sim_object.id)
        SimObject.objects.filter(id__in=ids_to_delete).delete()
        return len(results_queryset) - len(ids_to_delete), page_count

    def delete_object(self, id):
        subject = SimObject.objects.filter(
            id=id).first()
        if subject:
            subject.delete()
            return True
        return False
