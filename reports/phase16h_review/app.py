import os
import sys
import json
import csv
import datetime
import time
from flask import Flask, render_template, request, redirect, url_for, jsonify

BASE_DIR_PROJ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR_PROJ)

from src.threadmind.router.fallback_router import FallbackRouter
from src.threadmind.rag.dense_retriever import DenseRetriever
from src.threadmind.llm.provider import LLMProvider

# Lazy loaded components
_router = None
_retriever = None
_llm = None

def get_router():
    global _router
    if _router is None: _router = FallbackRouter()
    return _router

def get_retriever():
    global _retriever
    if _retriever is None: _retriever = DenseRetriever()
    return _retriever

def get_llm():
    global _llm
    if _llm is None: _llm = LLMProvider()
    return _llm


app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(BASE_DIR, "phase16h_human_review_workbench.json")
BASELINES_PATH = os.path.join(BASE_DIR, "phase16h_verification/phase16j_baselines.json")
if not os.path.exists(BASELINES_PATH):
    BASELINES_PATH = os.path.join(BASE_DIR, "phase16j_baselines.json")
TAXONOMY_AUDIT_PATH = os.path.join(BASE_DIR, "phase16e_taxonomy_audit.json")

TEST_MODE = os.environ.get("THREADMIND_TEST_MODE") == "1"
if "THREADMIND_CSV_PATH" in os.environ:
    CSV_PATH = os.path.join(BASE_DIR, os.environ["THREADMIND_CSV_PATH"])
elif TEST_MODE:
    CSV_PATH = os.path.join(BASE_DIR, "reports/phase16h_verification/test_data/test_human_decisions.csv")
else:
    CSV_PATH = os.path.join(BASE_DIR, "reports/phase16h_human_decisions.csv")

os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
BACKUP_PATH = CSV_PATH.replace(".csv", "_backup.csv")

TAXONOMY = [
    "account_access", "account_billing", "returns_refunds", "promotions_pricing",
    "delivery_missing", "delivery_wrong_item", "grocery_fresh", "amazon_locker",
    "delivery_delayed", "echo_alexa", "digital_prime_video", "digital_kindle",
    "amazon_music", "product_availability", "other_support"
]

def load_cases():
    with open(JSON_PATH, "r") as f:
        return json.load(f)

def load_decisions():
    decisions = {}
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                decisions[row["case_id"]] = row
    return decisions

def save_decision(case_id, current_label, human_decision, new_label, human_reason, confidence="", reviewer=""):
    decisions = load_decisions()
    
    # Check if we're overwriting something that is not PENDING
    existing = decisions.get(case_id, {})
    if existing.get("human_decision", "PENDING") != "PENDING" and existing.get("human_decision") != human_decision:
        print(f"Overwriting previous decision for {case_id}")
        
    decisions[case_id] = {
        "case_id": case_id,
        "current_label": current_label,
        "proposed_label": new_label,
        "human_decision": human_decision,
        "human_reason": human_reason,
        "confidence": confidence if confidence else "HIGH",
        "reviewer": reviewer if reviewer else os.environ.get("REVIEWER", "Developer"),
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    headers = ["case_id", "current_label", "proposed_label", "human_decision", "human_reason", "confidence", "reviewer", "timestamp"]
    
    # Save to main
    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for cid in sorted(decisions.keys()):
            writer.writerow(decisions[cid])
            
    # Save to backup
    with open(BACKUP_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for cid in sorted(decisions.keys()):
            writer.writerow(decisions[cid])

@app.route("/")
def index():
    return redirect("/case/0")

@app.route("/dashboard")
def dashboard():
    cases = load_cases()
    decisions = load_decisions()
    
    # Load baselines for metrics
    v2_metrics = {}
    try:
        with open(BASELINES_PATH, "r") as f:
            baselines = json.load(f)
            v2_metrics = baselines.get("v2", {})
    except Exception:
        pass
        
    return render_template(
        "dashboard.html",
        cases=cases,
        decisions=decisions,
        v2_metrics=v2_metrics,
        golden_set_size=196,
        TEST_MODE=TEST_MODE,
        active_page="dashboard"
    )

@app.route("/playground", methods=["GET"])
def playground():
    return render_template("playground.html", active_page="playground")

@app.route("/api/playground/analyze", methods=["POST"])
def api_playground_analyze():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid JSON payload"}), 400
            
        query = data.get("query", "").strip()
        if not query:
            return jsonify({"success": False, "error": "Query cannot be empty"}), 400
            
        start_time = time.time()
        router = get_router()
        retriever = get_retriever()
        llm = get_llm()
        
        # Create conversation object
        conv = [{"author": "customer", "inbound": True, "text": query}]
        
        # Predict intent
        pred = router.predict(conv)
        intent = pred.get("predicted_intent", "unknown")
        conf = pred.get("confidence", 0.0)
        if intent != "other_support" and conf == 0.0:
            conf = 0.95  # Heuristic for rule router
        
        # Retrieve
        retrieved_docs = retriever.retrieve(conv, k=3)
        
        retrieved_with_scores = [
            {
                "text": json.dumps(d['metadata']['conversation']),
                "score": float(d['score']),
                "intent": d['metadata'].get('intent', 'unknown')
            }
            for d in retrieved_docs
        ]
        
        # Use generate_and_judge_responses logic
        conv_str = json.dumps(conv, indent=2)
        ev_str = ""
        for i, doc_obj in enumerate(retrieved_with_scores):
            ev_str += f"--- Example {i+1} ---\n{doc_obj['text']}\n\n"
            
        prompt = f"""You are an expert Amazon Customer Support AI agent.
Your task is to generate a grounded, empathetic, and professional response to the customer, OR escalate the issue if you lack sufficient information or authority.

Intent: {intent}

Customer Conversation:
{conv_str}

Retrieved Historical Evidence (for tone and policy grounding):
{ev_str}

Respond in STRICT JSON format:
{{
  "response": "Your generated Amazon customer support response. If escalating, explain why to the customer politely.",
  "escalation": "AUTO_HANDLE or ESCALATE",
  "escalation_reason": "Explanation of why you chose to auto-handle or escalate."
}}

Rules:
- NEVER invent refund amounts, delivery dates, or personal account details.
- You do NOT have access to a database or user accounts. You cannot look up orders, process refunds, or secure accounts.
- ESCALATION POLICY: You MUST output "ESCALATE" for the escalation field if the customer's request involves ANY of the following:
  1) An order number or tracking ID.
  2) A refund, charge, billing dispute, or unrecognized transaction.
  3) Unauthorized account access, account security, or hacked accounts.
  4) Changing account details, payment methods, or passwords.
  Do NOT attempt to auto-handle these. You CANNOT process these requests. Output "ESCALATE" immediately.
- Only output "AUTO_HANDLE" for general troubleshooting, FAQs, or generic return policy questions that do not require account access.
- Maintain Amazon brand voice (polite, helpful, concise).
"""
        try:
            llm_json = llm.predict(prompt, json_mode=True)
            if "error" in llm_json:
                llm_response = ""
                escalate = False
                escalation_reason = llm_json.get("error", "LLM Unavailable")
                llm_error = True
            else:
                llm_response = llm_json.get("response", "")
                escalate_str = llm_json.get("escalation", "")
                escalate = (escalate_str == "ESCALATE")
                escalation_reason = llm_json.get("escalation_reason", "")
                llm_error = False
        except Exception as e:
            llm_response = ""
            escalate = False
            escalation_reason = "LLM Unavailable"
            llm_error = True
        
        latency = time.time() - start_time
            
        return jsonify({
            "success": True,
            "query": query,
            "intent": intent,
            "confidence": round(conf * 100, 1),
            "retrieval": retrieved_with_scores,
            "response": llm_response,
            "escalate": escalate,
            "escalation_reason": escalation_reason,
            "llm_error": llm_error,
            "latency": round(latency, 2)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/conversations")
def conversations():
    cases = load_cases()
    return render_template("conversations.html", active_page="conversations", cases=cases)

@app.route("/retrieval", methods=["GET", "POST"])
def retrieval():
    result = None
    if request.method == "POST":
        query = request.form.get("query", "").strip()
        if query:
            start_time = time.time()
            retriever = get_retriever()
            conv = [{"author": "customer", "inbound": True, "text": query}]
            retrieved_docs = retriever.retrieve(conv, k=5)
            docs_with_scores = [(d, float(d['score'])) for d in retrieved_docs]
                
            latency = time.time() - start_time
            result = {
                "query": query,
                "docs": docs_with_scores,
                "latency": round(latency, 2)
            }
    return render_template("retrieval.html", active_page="retrieval", result=result)

@app.route("/classifier", methods=["GET", "POST"])
def classifier():
    result = None
    if request.method == "POST":
        query = request.form.get("query", "").strip()
        if query:
            start_time = time.time()
            router = get_router()
            conv = [{"author": "customer", "inbound": True, "text": query}]
            pred = router.predict(conv)
            intent = pred.get("predicted_intent", "unknown")
            conf = pred.get("confidence", 0.0)
            if intent != "other_support" and conf == 0.0:
                conf = 0.95
                
            latency = time.time() - start_time
            result = {
                "query": query,
                "intent": intent,
                "confidence": round(conf * 100, 1),
                "latency": round(latency, 2)
            }
    return render_template("classifier.html", active_page="classifier", taxonomy=TAXONOMY, result=result)

@app.route("/knowledge")
def knowledge():
    return render_template("knowledge.html", active_page="knowledge")

@app.route("/monitoring")
def monitoring():
    # Simple ping tests
    ollama_status = "OFFLINE"
    try:
        import requests
        if requests.get("http://localhost:11434", timeout=2).status_code == 200:
            ollama_status = "ONLINE"
    except: pass
    
    faiss_status = "LOADED" if _retriever is not None else "READY (Lazy)"
    model_status = "LOADED" if _router is not None else "READY (Lazy)"
    
    return render_template("monitoring.html", active_page="monitoring", 
                           ollama_status=ollama_status, 
                           faiss_status=faiss_status, 
                           model_status=model_status)

@app.route("/settings")
def settings():
    return render_template("settings.html", active_page="settings")

@app.route("/case/<int:index>")
def view_case(index):
    cases = load_cases()
    decisions = load_decisions()
    
    if index < 0:
        return redirect(url_for("view_case", index=0))
    if index >= len(cases):
        return redirect(url_for("done"))
        
    case = cases[index]
    decision = decisions.get(case["id"], {})
    
    completed = sum(1 for d in decisions.values() if d.get("human_decision", "PENDING") != "PENDING")
    
    return render_template(
        "index.html",
        case=case,
        decision=decision,
        index=index,
        total=len(cases),
        completed=completed,
        taxonomy=TAXONOMY,
        all_cases=cases,
        all_decisions=decisions,
        active_page="evaluation"
    )

@app.route("/case/<int:index>/save", methods=["POST"])
def save_case(index):
    cases = load_cases()
    if index >= len(cases):
        return redirect(url_for("done"))
        
    case = cases[index]
    human_decision = request.form.get("human_decision")
    new_label = request.form.get("new_label", "")
    human_reason = request.form.get("human_reason", "")
    
    if human_decision != "CHANGE_LABEL":
        new_label = ""
        
    form_confidence = request.form.get("confidence", "")
    form_reviewer = request.form.get("reviewer", "")
        
    save_decision(case["id"], case["current_label"], human_decision, new_label, human_reason, form_confidence, form_reviewer)
    return redirect(url_for("view_case", index=index + 1))

@app.route("/done")
def done():
    decisions = load_decisions()
    completed = len(decisions)
    counts = {
        "KEEP_CURRENT_LABEL": 0,
        "CHANGE_LABEL": 0,
        "AMBIGUOUS_KEEP": 0,
        "INSUFFICIENT_EVIDENCE": 0
    }
    for row in decisions.values():
        val = row.get("human_decision", "")
        if val in counts:
            counts[val] += 1
            
    return render_template(
        "done.html",
        completed=completed,
        total=len(load_cases()),
        counts=counts,
        TEST_MODE=TEST_MODE
    )

if __name__ == "__main__":
    app.run(port=5001, debug=True, use_reloader=False)
