import os
import json
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from src.threadmind import config
from src.threadmind.baselines.rule_baseline import RuleBaseline

class DenseRetriever:
    def __init__(self, corpus_path=None, model_name="all-MiniLM-L6-v2"):
        self.corpus_path = corpus_path or config.PROCESSED_DATA_DIR / "retrieval_corpus.jsonl"
        self.cache_dir = config.PROJECT_ROOT / ".cache" / "rag_dense"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.index_path = self.cache_dir / "faiss_index.bin"
        self.corpus_metadata_path = self.cache_dir / "corpus_metadata.pkl"
        
        self.model_name = model_name
        import torch
        device = "mps" if torch.backends.mps.is_available() else "cpu"
        print(f"Loading SentenceTransformer on device: {device}")
        self.model = SentenceTransformer(model_name, device=device)
        
        self.index = None
        self.corpus_metadata = None
        
        self._load_or_build_index()

    def _format_conversation(self, conversation):
        text_parts = []
        for msg in conversation:
            is_inbound = msg.get("inbound")
            if is_inbound is not None:
                role = "User" if is_inbound else "Agent"
            else:
                role = "Agent" if msg.get("author_role") == "agent" else "User"
            text_parts.append(f"{role}: {msg.get('text', '')}")
        return "\n".join(text_parts)

    def _load_or_build_index(self):
        if os.path.exists(self.index_path) and os.path.exists(self.corpus_metadata_path):
            self.index = faiss.read_index(str(self.index_path))
            with open(self.corpus_metadata_path, "rb") as f:
                self.corpus_metadata = pickle.load(f)
        else:
            self._build_index()

    def _build_index(self):
        print(f"Building Dense Index from {self.corpus_path} using {self.model_name}...")
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
                    
        print(f"Encoding {len(corpus_texts)} threads (this may take a few minutes)...")
        # Encode all texts
        embeddings = self.model.encode(corpus_texts, show_progress_bar=True, batch_size=32)
        embeddings = np.array(embeddings).astype('float32')
        
        print("Building FAISS index...")
        # L2 normalized vectors for Cosine Similarity search using Inner Product
        faiss.normalize_L2(embeddings)
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings)
        
        # Save
        faiss.write_index(self.index, str(self.index_path))
        with open(self.corpus_metadata_path, "wb") as f:
            pickle.dump(self.corpus_metadata, f)
            
        print("Dense Index saved successfully.")

    def retrieve(self, conversation, k=3):
        query_text = self._format_conversation(conversation)
        query_vec = self.model.encode([query_text])
        query_vec = np.array(query_vec).astype('float32')
        faiss.normalize_L2(query_vec)
        
        scores, indices = self.index.search(query_vec, k)
        
        results = []
        for i in range(k):
            idx = indices[0][i]
            score = scores[0][i]
            results.append({
                "score": float(score),
                "metadata": self.corpus_metadata[idx]
            })
            
        return results
