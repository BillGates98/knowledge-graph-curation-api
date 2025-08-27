import json
from SPARQLWrapper import SPARQLWrapper, JSON
from api.models import ComputationStatus, KnowledgeGraph, SimSubject, Subject
from api.services.lsh_services import LSHService


class SubjectService:

    def __init__(self, kg_name=None):
        self.kg_name = kg_name
        print(f"Initializing SubjectService for KG: {kg_name}")
        self.kg_model = KnowledgeGraph.objects.filter(
            name=kg_name).select_related('sparqlEndpointId').first()

    def get_offset_and_limit(self, page, limit, results_queryset):
        if limit < 0:
            offset = 0
            limit = len(results_queryset)
        else:
            offset = (page - 1) * limit
        return offset, limit

    def get_all_subjects(self):
        output = []
        kg_model = self.kg_model
        sparql = SPARQLWrapper(kg_model.sparqlEndpointId.uri)
        sparql.setQuery(f"""
            SELECT ?subject WHERE {{
                GRAPH <{kg_model.name}> {{
                    ?subject ?predicate ?object
                }}
            }}
        """)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        for result in results["results"]["bindings"]:
            subject_name = result["subject"]["value"]
            check = Subject.objects.filter(
                uri=subject_name, knowledgeGraphId=self.kg_model.id).exists()
            if not check:
                _subject = Subject(
                    uri=subject_name, knowledgeGraphId=self.kg_model)
                _subject.save()
        output = Subject.objects.filter(
            knowledgeGraphId=self.kg_model).values()
        print(f"Fetched {len(output)} subjects for KG: {self.kg_name}")
        return output

    def compute_subject_similarities(self):
        subjects = Subject.objects.filter(
            knowledgeGraphId=self.kg_model.id).values()
        if not subjects or len(subjects) == 0:
            print(f"No subjects found for KG: {self.kg_name}")
            subjects = self.get_all_subjects()

        print(f"Fetched {len(subjects)} subjects for KG: {self.kg_name}")
        corpus = [result['uri'] for result in subjects]
        computationStatus = ComputationStatus.objects.filter(
            knowledgeGraph=self.kg_model.id, axis='subject').first()

        if not computationStatus:
            computationStatus = ComputationStatus(
                knowledgeGraph=self.kg_model.id, axis='subject', status='BLSHING')
            computationStatus.save()
        # Simulate computation delay
        print(f"Total corpus : {len(corpus)}")
        lshService = LSHService(corpus=corpus)
        computationStatus.status = 'in_progress'
        computationStatus.save()
        for result in lshService.run():
            # save to SimSubject
            if result['source'] != result['target']:
                check = SimSubject.objects.filter(
                    subjectId__uri=result['source'], uri=result['target'], subjectId__knowledgeGraphId=self.kg_model.id).exists()
                if not check:
                    _source = Subject.objects.filter(
                        uri=result['source'], knowledgeGraphId=self.kg_model.id).first()
                    _target = Subject.objects.filter(
                        uri=result['target'], knowledgeGraphId=self.kg_model.id).first()
                    _subject = SimSubject(
                        subjectId=_source, uri=_target.uri, score=result['sim_score'])
                    _subject.save()
            # Update progress
            computationStatus.progress += (1.0 / len(corpus)) * 100
            computationStatus.save()

        computationStatus.status = 'Completed'
        computationStatus.save()
        return computationStatus

    def fetch_subjects(self):
        results = self.get_all_subjects()
        return results

    def fetch_similar_subjects(self, min_score=0.0, max_score=1.0, limit=100, page=1):
        results_queryset = SimSubject.objects.filter(
            score__gte=min_score,
            score__lte=max_score,
            subjectId__knowledgeGraphId=self.kg_model.id
        ).order_by('-score').select_related('subjectId')  # .values()
        page_count = (len(results_queryset) + limit -
                      1) // limit if limit > 0 else 1
        page = max(1, min(page, page_count))  # Ensure page is within bounds
        offset, limit = self.get_offset_and_limit(
            page, limit, results_queryset)
        final_results = []
        for sim_subject in results_queryset[offset:offset + limit]:
            final_results.append({
                "sim_subject_id": sim_subject.id,
                "sim_subject_uri": sim_subject.uri,
                "subject_uri": sim_subject.subjectId.uri,
                "subject_id": sim_subject.subjectId.id,
                "score": sim_subject.score
            })
        return final_results, len(results_queryset), page_count

    def generate_correspondences(self, min_score=0.0, max_score=1.0, limit=100, page=1):
        correspondences = []
        queries = []
        correspondence_file_path = f"/tmp/correspondences_kg_{self.kg_model.id}_m_{min_score}_M_{max_score}_l_{limit}_p_{page}.json"
        query_file_path = f"/tmp/subject_update_queries_kg_{self.kg_model.id}_m_{min_score}_M_{max_score}_l_{limit}_p_{page}.sparql"
        results, _, _ = self.fetch_similar_subjects(
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
        template = "\nDELETE { <%s> ?p ?o . }\n INSERT { <%s> ?p ?o . }\nWHERE  { <%s> ?p ?o . };\n"
        if alignment:
            return template % (alignment['subject_uri'], alignment['sim_subject_uri'], alignment['subject_uri'])
        return None

    def delete_similar_subjects(self, min_score=0.0, max_score=1.0, limit=100, page=1):
        results_queryset = SimSubject.objects.filter(
            score__gte=min_score,
            score__lte=max_score,
            subjectId__knowledgeGraphId=self.kg_model.id
        ).select_related('subjectId')
        page_count = (len(results_queryset) + limit -
                      1) // limit if limit > 0 else 1
        page = max(1, min(page, page_count))  # Ensure page is within bounds
        offset, limit = self.get_offset_and_limit(
            page, limit, results_queryset)
        ids_to_delete = []
        for sim_subject in results_queryset[offset:offset + limit]:
            ids_to_delete.append(sim_subject.id)
        SimSubject.objects.filter(id__in=ids_to_delete).delete()
        return len(results_queryset) - len(ids_to_delete), page_count
