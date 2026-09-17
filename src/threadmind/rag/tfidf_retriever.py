import os
import json
import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from src.threadmind import config
from src.threadmind.baselines.rule_baseline import RuleBaseline

class TFIDFRetriever:
    def __init__(self, corpus_path=None):
        self.corpus_path = corpus_path or config.PROCESSED_DATA_DIR / "retrieval_corpus.jsonl"
        self.cache_dir = config.PROJECT_ROOT / ".cache" / "rag"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.vectorizer_path = self.cache_dir / "tfidf_vectorizer.pkl"
        self.index_path = self.cache_dir / "tfidf_matrix.pkl"
        self.corpus_metadata_path = self.cache_dir / "corpus_metadata.pkl"
        
        self.vectorizer = None
        self.tfidf_matrix = None
        self.corpus_metadata = None
        
        self._load_or_build_index()

    def _format_conversation(self, conversation):
        text_parts = []
        for msg in conversation:
            # Handle both golden set format ("author_role": "customer"/"agent") and raw format
            is_inbound = msg.get("inbound")
            if is_inbound is not None:
                role = "User" if is_inbound else "Agent"
            else:
                role = "Agent" if msg.get("author_role") == "agent" else "User"
            text_parts.append(f"{role}: {msg.get('text', '')}")
        return "\n".join(text_parts)

    def _load_or_build_index(self):
        if (os.path.exists(self.vectorizer_path) and 
            os.path.exists(self.index_path) and 
            os.path.exists(self.corpus_metadata_path)):
            
            with open(self.vectorizer_path, "rb") as f:
                self.vectorizer = pickle.load(f)
            with open(self.index_path, "rb") as f:
                self.tfidf_matrix = pickle.load(f)
            with open(self.corpus_metadata_path, "rb") as f:
                self.corpus_metadata = pickle.load(f)
        else:
            self._build_index()

    def _build_index(self):
        print("Building TF-IDF Index from retrieval corpus...")
        self.corpus_metadata = []
        corpus_texts = []
        
        rule_system = RuleBaseline()
        
        with open(self.corpus_path, "r") as f:
            for i, line in enumerate(f):
                thread = json.loads(line)
                
                # Weak labeling via rule baseline
                conv = []
                for m in thread['messages']:
                    is_inbound = m.get('inbound', True)
                    conv.append({
                        "author_role": "customer" if is_inbound else "agent",
                        "text": m['text']
                    })
                    
                pred = rule_system.predict(conv)
                label = pred['predicted_intent']
                escalation = pred['predicted_escalation']
                
                if label != "other_support":
                    text = self._format_conversation(thread["messages"])
                    corpus_texts.append(text)
                    self.corpus_metadata.append({
                        "thread_id": thread["thread_id"],
                        "intent_id": label,
                        "escalation": escalation,
                        "conversation": text
                    })
                    
                if (i+1) % 10000 == 0:
                    print(f"Processed {i+1} threads...")
                    
        print(f"Fitting TfidfVectorizer on {len(corpus_texts)} threads...")
        self.vectorizer = TfidfVectorizer(max_features=50000)
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus_texts)
        
        with open(self.vectorizer_path, "wb") as f:
            pickle.dump(self.vectorizer, f)
        with open(self.index_path, "wb") as f:
            pickle.dump(self.tfidf_matrix, f)
        with open(self.corpus_metadata_path, "wb") as f:
            pickle.dump(self.corpus_metadata, f)
            
        print("TF-IDF Index saved successfully.")

    def retrieve(self, conversation, k=3):
        query_text = self._format_conversation(conversation)
        query_vec = self.vectorizer.transform([query_text])
        
        # Calculate cosine similarity between query and all documents
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        # Get top-k indices
        # argpartition is faster than argsort for top-k
        if len(similarities) < k:
            k = len(similarities)
            
        top_k_indices = np.argpartition(similarities, -k)[-k:]
        # Sort them in descending order
        top_k_indices = top_k_indices[np.argsort(-similarities[top_k_indices])]
        
        results = []
        for idx in top_k_indices:
            results.append({
                "score": float(similarities[idx]),
                "metadata": self.corpus_metadata[idx]
            })
            
        return results
