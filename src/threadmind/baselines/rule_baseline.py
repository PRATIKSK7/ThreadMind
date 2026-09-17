import re

class RuleBaseline:
    def __init__(self):
        self.INTENT_KEYWORDS = {
            "delivery_wrong_item": ["wrong item", "incorrect", "not what i ordered", "different item"],
            "delivery_missing": ["delivered", "not here", "missing package", "stolen", "didn't receive", "empty box", "never received"],
            "delivery_delayed": ["late", "delay", "not arrived", "still waiting", "taking too long"],
            "returns_refunds": ["return", "refund", "label", "defective", "broken"],
            "account_billing": ["charge", "billed", "unauthorized", "bank", "money", "subscription"],
            "digital_prime_video": ["video", "movie", "streaming", "prime video", "playback"],
            "digital_kindle": ["kindle", "ebook", "paperwhite", "library", "downloading book"],
            "amazon_music": ["music", "song", "playlist", "amazon music"],
            "echo_alexa": ["echo", "alexa", "dot", "device not responding"],
            "account_access": ["login", "password", "locked", "access", "can't sign in", "app crashing"],
            "promotions_pricing": ["discount", "promo", "price", "deal", "coupon"],
            "amazon_locker": ["locker", "access code", "pick up"],
            "grocery_fresh": ["fresh", "whole foods", "grocery", "spoiled", "food", "delivery window"],
            "product_availability": ["stock", "pre-order", "available"]
        }

    def predict(self, conversation_history: list[dict]) -> dict:
        """
        Takes a conversation list like [{'author_role': 'customer', 'text': '...'}, ...]
        Returns the standard prediction schema.
        """
        try:
            # Extract customer text
            customer_text = " ".join([m['text'].lower() for m in conversation_history if m['author_role'] == 'customer'])
            
            # Predict Intent
            matched_intents = []
            
            # Match keywords
            for intent, keywords in self.INTENT_KEYWORDS.items():
                if any(kw in customer_text for kw in keywords):
                    matched_intents.append(intent)
                    
            if len(matched_intents) == 1:
                predicted_intent = matched_intents[0]
                confidence = 1.0
            else:
                # Abstain on collision (>= 2) or no match (0)
                predicted_intent = "other_support"
                confidence = 0.0
            
            # Predict Escalation
            predicted_escalation = "no_escalation"
            if any(k in customer_text for k in ["real person", "human", "agent", "supervisor", "manager", "fraud"]):
                predicted_escalation = "human_review_recommended"
            elif customer_text.count("didn't work") >= 2 or customer_text.count("still not") >= 2:
                predicted_escalation = "human_review_recommended"
            elif any(k in customer_text for k in ["where is my", "tracking", "status"]) and not any(char.isdigit() for char in customer_text):
                predicted_escalation = "clarification_needed"
                
            return {
                "predicted_intent": predicted_intent,
                "confidence": confidence,
                "predicted_escalation": predicted_escalation,
                "reasoning_summary": f"Keyword matching heuristics. Intent matched: {predicted_intent != 'other_support'}",
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
