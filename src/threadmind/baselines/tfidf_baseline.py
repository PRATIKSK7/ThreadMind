from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import joblib

class TfidfBaseline:
    def __init__(self, vectorizer_path=None, model_path=None):
        if vectorizer_path and model_path:
            self.vectorizer = joblib.load(vectorizer_path)
            self.model = joblib.load(model_path)
        else:
            self.vectorizer = TfidfVectorizer(stop_words='english', max_features=5000, ngram_range=(1, 2))
            self.model = LogisticRegression(max_iter=1000, class_weight='balanced')
            
    def train(self, texts, labels):
        X = self.vectorizer.fit_transform(texts)
        self.model.fit(X, labels)
        
    def save(self, vectorizer_path, model_path):
        joblib.dump(self.vectorizer, vectorizer_path)
        joblib.dump(self.model, model_path)
        
    def predict(self, conversation_history: list[dict]) -> dict:
        try:
            customer_text = " ".join([m['text'].lower() for m in conversation_history if m['author_role'] == 'customer'])
            X = self.vectorizer.transform([customer_text])
            
            predicted_intent = self.model.predict(X)[0]
            probs = self.model.predict_proba(X)[0]
            confidence = max(probs)
            
            # The TF-IDF model only predicts intent for now, we use a default fallback for escalation
            return {
                "predicted_intent": predicted_intent,
                "confidence": float(confidence),
                "predicted_escalation": "no_escalation", # ML baseline focuses on intent
                "reasoning_summary": "TF-IDF Logistic Regression prediction.",
                "error": None
            }
        except Exception as e:
            return {
                "predicted_intent": "other_support",
                "confidence": 0.0,
                "predicted_escalation": "no_escalation",
                "reasoning_summary": "",
                "error": str(e)
            }
