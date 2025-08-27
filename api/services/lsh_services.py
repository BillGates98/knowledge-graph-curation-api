import re
from datasketch import MinHash, MinHashLSH
import time


class LSHService:

    def __init__(self, corpus=[]):
        self.corpus = corpus
        self.lsh = self.build_lsh_index()
        print(f"Total pairs: {len(corpus)*len(corpus)} elements to compare.")

    def preprocess_string(self, s):
        s = re.sub(r'[^\w\s]', '', s.lower())
        shingles = set()
        for i in range(len(s) - 2):
            shingles.add(s[i:i+3])
        return shingles

    def jaccard_similarity(self, set1, set2):
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0

    def build_lsh_index(self, num_perm=128, threshold=0.5):
        start_time = time.time()
        print("Creation of LSH index")
        lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
        minhashes = {}
        for i, s in enumerate(self.corpus):
            m = MinHash(num_perm=num_perm)
            shingles = self.preprocess_string(s)
            if shingles:
                for shingle in shingles:
                    m.update(shingle.encode('utf-8'))
                minhashes[f"doc_{i}"] = m

        with lsh.insertion_session() as session:
            for key, minhash in minhashes.items():
                session.insert(key, minhash)

        print(f"Index LSH créé en {time.time() - start_time:.2f} secondes.")
        return lsh

    def search_candidates(self, query, lsh):
        query_shingles = self.preprocess_string(query)
        if not query_shingles:
            return []

        query_minhash = MinHash(num_perm=128)
        for shingle in query_shingles:
            query_minhash.update(shingle.encode('utf-8'))

        candidate_docs = lsh.query(query_minhash)
        return candidate_docs, query_shingles

    def one_comparison(self, query, lsh):
        results = []
        candidates, query_shingles = self.search_candidates(query, lsh)
        for key in candidates:
            doc_index = int(key.split('_')[1])
            doc_shingles = self.preprocess_string(self.corpus[doc_index])
            sim_score = self.jaccard_similarity(query_shingles, doc_shingles)
            results.append({
                "source": query,
                "target": self.corpus[doc_index],
                "sim_score": sim_score
            })
        return results

    def run(self):
        print("Starting LSH similarity computation...")
        start_time = time.time()
        for query in self.corpus:
            yield from self.one_comparison(query, self.lsh)
        print(
            f"LSH similarity computation completed in {time.time() - start_time:.2f} seconds.")
