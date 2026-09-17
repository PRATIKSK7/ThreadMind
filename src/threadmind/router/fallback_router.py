import json
from src.threadmind import config
from src.threadmind.baselines.tfidf_baseline import TfidfBaseline
from src.threadmind.baselines.rule_baseline import RuleBaseline
from src.threadmind.rag.dense_retriever import DenseRetriever
from src.threadmind.llm.provider import LLMProvider

class FallbackRouter:
    def __init__(self, k=3, confidence_threshold=0.70):
        self.k = k
        self.confidence_threshold = confidence_threshold
        
        print("Initializing TF-IDF Confidence Model...")
        self.tfidf_system = TfidfBaseline(
            vectorizer_path=config.PROCESSED_DATA_DIR / "tfidf_vectorizer.joblib",
            model_path=config.PROCESSED_DATA_DIR / "tfidf_model.joblib"
        )
        
        # We keep RuleBaseline for supporting signals if needed
        self.rule_system = RuleBaseline()
        
        print("Initializing Dense Retriever...")
        self.retriever = DenseRetriever()
        
        print("Initializing LLM Provider...")
        self.llm = LLMProvider()
        
        # Load prompt template
        prompt_path = config.PROJECT_ROOT / "src" / "threadmind" / "llm" / "prompts" / "rag_classification_v1.txt"
        with open(prompt_path, "r") as f:
            self.prompt_template = f.read()
            
    def _format_few_shot(self, retrieved_docs):
        blocks = []
        for i, doc in enumerate(retrieved_docs):
            meta = doc['metadata']
            block = f"--- Example {i+1} ---\n"
            block += f"Conversation:\n{meta['conversation']}\n\n"
            block += f"Classification:\n"
            block += f"{{\n  \"predicted_intent\": \"{meta['intent_id']}\",\n"
            block += f"  \"predicted_escalation\": \"{meta['escalation']}\"\n}}\n"
            blocks.append(block)
        return "\n".join(blocks)
            
    def predict(self, conversation):
        rule_conv = []
        for m in conversation:
            is_inbound = m.get('inbound')
            if is_inbound is not None:
                role = "customer" if is_inbound else "agent"
            else:
                role = m.get('author_role', 'customer')
            rule_conv.append({"author_role": role, "text": m.get('text', '')})
            
        # 1. Rule First Layer
        rule_pred = self.rule_system.predict(rule_conv)
        if rule_pred['predicted_intent'] != "other_support":
            rule_pred['routed_via'] = "RuleBaseline"
            return rule_pred
            
        # 2. Ask TF-IDF Model for prediction and confidence
        tfidf_pred = self.tfidf_system.predict(rule_conv)
        confidence = tfidf_pred.get('confidence', 0.0)
        
        # 3. Check if TF-IDF is confident
        if confidence >= self.confidence_threshold and tfidf_pred['predicted_intent'] != "other_support":
            tfidf_pred['routed_via'] = "TFIDFBaseline"
            return tfidf_pred
            
        # 3. Fallback to Dense RAG LLM
        retrieved_docs = self.retriever.retrieve(conversation, k=self.k)
        few_shot_str = self._format_few_shot(retrieved_docs)
        
        conv_str = json.dumps(conversation, indent=2)
        prompt = self.prompt_template.replace("{few_shot_examples}", few_shot_str)
        prompt = prompt.replace("{conversation}", conv_str)
        
        llm_pred = self.llm.predict(prompt)
        llm_pred['routed_via'] = "DenseRAG_LLM"
        
        # Ensure safe fallback if LLM crashes or returns malformed response
        if "error" in llm_pred or "predicted_intent" not in llm_pred:
            llm_pred['predicted_intent'] = "other_support"
            
        return llm_pred
