import json
from SPARQLWrapper import SPARQLWrapper, JSON
from api.models import ComputationStatus, KnowledgeGraph, SimPredicate, Predicate
from api.services.lsh_services import LSHService


class PredicateService:

    def __init__(self, kg_name=None):
        self.kg_name = kg_name
        print(f"Initializing PredicateService for KG: {kg_name}")
        self.kg_model = KnowledgeGraph.objects.filter(
            name=kg_name).select_related('sparqlEndpointId').first()

    def get_offset_and_limit(self, page, limit, results_queryset):
        if limit < 0:
            offset = 0
            limit = len(results_queryset)
        else:
            offset = (page - 1) * limit
        return offset, limit

    def get_all_predicates(self):
        output = []
        kg_model = self.kg_model
        sparql = SPARQLWrapper(kg_model.sparqlEndpointId.uri)
        sparql.setQuery(f"""
            SELECT ?predicate WHERE {{
                GRAPH <{kg_model.name}> {{
                    ?subject ?predicate ?object
                }}
            }}
        """)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        for result in results["results"]["bindings"]:
            predicate_name = result["predicate"]["value"]
            check = Predicate.objects.filter(
                uri=predicate_name, knowledgeGraphId=self.kg_model.id).exists()
            if not check:
                _predicate = Predicate(
                    uri=predicate_name, knowledgeGraphId=self.kg_model)
                _predicate.save()
        output = Predicate.objects.filter(
            knowledgeGraphId=self.kg_model).values()
        print(f"Fetched {len(output)} predicates for KG: {self.kg_name}")
        return output

    def compute_predicate_similarities(self):
        predicates = Predicate.objects.filter(
            knowledgeGraphId=self.kg_model.id).values()
        if not predicates or len(predicates) == 0:
            print(f"No predicates found for KG: {self.kg_name}")
            predicates = self.get_all_predicates()

        print(f"Fetched {len(predicates)} predicates for KG: {self.kg_name}")
        corpus = [result['uri'] for result in predicates]
        computationStatus = ComputationStatus.objects.filter(
            knowledgeGraph=self.kg_model.id, axis='predicate').first()

        if not computationStatus:
            computationStatus = ComputationStatus(
                knowledgeGraph=self.kg_model.id, axis='predicate', status='BLSHING')
            computationStatus.save()
        # Simulate computation delay
        print(f"Total corpus : {len(corpus)}")
        lshService = LSHService(corpus=corpus)
        computationStatus.status = 'IN_PROGRESS'
        computationStatus.save()
        for result in lshService.run():
            # save to SimPredicate
            if result['source'] != result['target']:
                check = SimPredicate.objects.filter(
                    predicateId__uri=result['source'], uri=result['target'], predicateId__knowledgeGraphId=self.kg_model.id).exists()
                if not check:
                    _source = Predicate.objects.filter(
                        uri=result['source'], knowledgeGraphId=self.kg_model.id).first()
                    _target = Predicate.objects.filter(
                        uri=result['target'], knowledgeGraphId=self.kg_model.id).first()
                    _predicate = SimPredicate(
                        predicateId=_source, uri=_target.uri, score=result['sim_score'])
                    _predicate.save()
            # Update progress
            computationStatus.progress += (1.0 / (len(corpus)**2)) * 100
            computationStatus.save()

        computationStatus.status = 'COMPLETED'
        computationStatus.save()
        return computationStatus

    def fetch_predicates(self):
        results = self.get_all_predicates()
        return results

    def fetch_similar_predicates(self, min_score=0.0, max_score=1.0, limit=100, page=1):
        results_queryset = SimPredicate.objects.filter(
            score__gte=min_score,
            score__lte=max_score,
            predicateId__knowledgeGraphId=self.kg_model.id
        ).order_by('-score').select_related('predicateId')  # .values()
        page_count = (len(results_queryset) + limit -
                      1) // limit if limit > 0 else 1
        page = max(1, min(page, page_count))  # Ensure page is within bounds
        offset, limit = self.get_offset_and_limit(
            page, limit, results_queryset)
        final_results = []
        for sim_predicate in results_queryset[offset:offset + limit]:
            final_results.append({
                "sim_predicate_id": sim_predicate.id,
                "sim_predicate_uri": sim_predicate.uri,
                "predicate_uri": sim_predicate.predicateId.uri,
                "predicate_id": sim_predicate.predicateId.id,
                "score": sim_predicate.score
            })
        return final_results, len(results_queryset), page_count

    def generate_correspondences(self, min_score=0.0, max_score=1.0, limit=100, page=1):
        correspondences = []
        queries = []
        correspondence_file_path = f"/tmp/predicate_correspondences_kg_{self.kg_model.id}_m_{min_score}_M_{max_score}_l_{limit}_p_{page}.json"
        query_file_path = f"/tmp/predicate_update_queries_kg_{self.kg_model.id}_m_{min_score}_M_{max_score}_l_{limit}_p_{page}.sparql"
        results, _, _ = self.fetch_similar_predicates(
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
        template = "\nDELETE { ?s <%s> ?o . }\nINSERT { ?s <%s> ?o . }\nWHERE  { ?s <%s> ?o . };\n"
        if alignment:
            return template % (alignment['predicate_uri'], alignment['sim_predicate_uri'], alignment['predicate_uri'])
        return None

    def delete_similar_predicates(self, min_score=0.0, max_score=1.0, limit=100, page=1):
        results_queryset = SimPredicate.objects.filter(
            score__gte=min_score,
            score__lte=max_score,
            predicateId__knowledgeGraphId=self.kg_model.id
        ).select_related('predicateId')
        page_count = (len(results_queryset) + limit -
                      1) // limit if limit > 0 else 1
        page = max(1, min(page, page_count))  # Ensure page is within bounds
        offset, limit = self.get_offset_and_limit(
            page, limit, results_queryset)
        ids_to_delete = []
        for sim_predicate in results_queryset[offset:offset + limit]:
            ids_to_delete.append(sim_predicate.id)
        SimPredicate.objects.filter(id__in=ids_to_delete).delete()
        return len(results_queryset) - len(ids_to_delete), page_count

    def delete_predicate(self, id):
        predicate = SimPredicate.objects.filter(
            id=id).first()
        if predicate:
            predicate.delete()
            return True
        return False
