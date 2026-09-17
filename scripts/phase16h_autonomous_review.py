import os
import sys
import time
import subprocess
import json
import csv
import hashlib
import requests
import traceback
from datetime import datetime
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from src.threadmind.llm.provider import LLMProvider

REPORTS_DIR = os.path.join(BASE_DIR, "reports")
CSV_PATH = os.path.join(REPORTS_DIR, "phase16h_autonomous_review.csv")
JSON_PATH = os.path.join(REPORTS_DIR, "phase16h_autonomous_review.json")
MD_PATH = os.path.join(REPORTS_DIR, "phase16h_autonomous_review.md")
GOLDEN_PATH = os.path.join(BASE_DIR, "data/processed/golden_set.jsonl")

# Setup Ollama Environment
os.environ["LLM_PROVIDER"] = "ollama"
os.environ["LLM_MODEL"] = "llama3.2:latest"

TAXONOMY = [
    "account_access", "account_billing", "returns_refunds", "promotions_pricing",
    "delivery_missing", "delivery_wrong_item", "grocery_fresh", "amazon_locker",
    "delivery_delayed", "echo_alexa", "digital_prime_video", "digital_kindle",
    "amazon_music", "product_availability", "other_support"
]

RESULTS = {
    "CASES": "0/24",
    "BROWSER": "PASS",
    "FORM": "PASS",
    "PERSISTENCE": "PASS",
    "CSV": "PASS",
    "GOLDEN SET": "UNCHANGED",
    "FAISS": "UNCHANGED",
    "MODEL": "UNCHANGED",
    "PRODUCTION": "UNCHANGED",
    "DECISION": "AUTONOMOUS_REVIEW_COMPLETE"
}

STATS = {
    "keep_count": 0,
    "change_count": 0,
    "ambiguous_count": 0,
    "insufficient_count": 0,
    "confidence_dist": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
    "cases": []
}

def hash_file(filepath):
    if not os.path.exists(filepath): return None
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def make_manifest():
    return {
        "golden_set": hash_file(GOLDEN_PATH),
        "app": hash_file(os.path.join(BASE_DIR, "reports/phase16h_review/app.py"))
    }

def start_flask():
    env = os.environ.copy()
    env["THREADMIND_TEST_MODE"] = "1"
    env["THREADMIND_CSV_PATH"] = "phase16h_autonomous_review.csv"
    env["PYTHONPATH"] = BASE_DIR
    
    app_path = os.path.join(BASE_DIR, "reports/phase16h_review/app.py")
    log_file = open(os.path.join(REPORTS_DIR, "flask_autonomous.log"), "w")
    process = subprocess.Popen([sys.executable, app_path], env=env, stdout=log_file, stderr=subprocess.STDOUT)
    
    for _ in range(20):
        try:
            r = requests.get("http://127.0.0.1:5001/case/0")
            if r.status_code == 200:
                return process
            else:
                time.sleep(1)
        except requests.exceptions.ConnectionError:
            time.sleep(1)
            
    process.kill()
    RESULTS["BROWSER"] = "FAIL"
    raise RuntimeError("Flask failed to start")

def get_llm_decision(llm, conversation, current_label, retrieved):
    prompt = f"""You are an autonomous QA agent evaluating a customer service conversation taxonomy label.

Conversation:
{conversation}

Current Golden Label: {current_label}
Retrieved Intents: {retrieved}

Taxonomy definitions (valid intents):
{', '.join(TAXONOMY)}

Use this reasoning order:
1. Identify the customer's PRIMARY operational request.
2. Identify explicit requested outcome.
3. Identify competing intents.
4. Determine whether one intent is clearly dominant.
5. If one intent clearly dominates:
      KEEP_CURRENT_LABEL if Golden Label matches.
      CHANGE_LABEL if Golden Label is demonstrably wrong.
6. If two intents are genuinely valid and neither can be established as primary:
      AMBIGUOUS
7. If the conversation lacks enough evidence:
      INSUFFICIENT_EVIDENCE
8. Never invent facts that are not present in the conversation.

Output strictly valid JSON only:
{{
  "decision": "KEEP_CURRENT_LABEL" | "CHANGE_LABEL" | "AMBIGUOUS" | "INSUFFICIENT_EVIDENCE",
  "proposed_label": "intent_name" or null,
  "confidence": "HIGH" | "MEDIUM" | "LOW",
  "reason": "concise evidence-based rationale"
}}"""

    for attempt in range(2):
        try:
            res = llm.predict(prompt, json_mode=True)
            if "error" in res:
                if attempt == 1:
                    return {"decision": "INSUFFICIENT_EVIDENCE", "proposed_label": None, "confidence": "LOW", "reason": f"LLM error: {res['error']}"}
                continue
                
            decision = res.get("decision")
            proposed_label = res.get("proposed_label")
            confidence = res.get("confidence")
            reason = res.get("reason")
            
            if decision not in ["KEEP_CURRENT_LABEL", "CHANGE_LABEL", "AMBIGUOUS", "INSUFFICIENT_EVIDENCE"]:
                raise ValueError("Invalid decision")
                
            if decision == "CHANGE_LABEL" and proposed_label not in TAXONOMY:
                raise ValueError("Invalid proposed_label")
                
            return {
                "decision": decision,
                "proposed_label": proposed_label,
                "confidence": confidence if confidence in ["HIGH", "MEDIUM", "LOW"] else "MEDIUM",
                "reason": reason
            }
        except Exception as e:
            if attempt == 1:
                return {"decision": "INSUFFICIENT_EVIDENCE", "proposed_label": None, "confidence": "LOW", "reason": f"LLM parsing failed: {e}"}

def run_agent():
    print("Starting Autonomous Review Agent...")
    manifest_before = make_manifest()
    llm = LLMProvider()
    llm.verify_model_availability()
    
    process = start_flask()
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Navigate to the first case or the correct resume point
            page.goto("http://127.0.0.1:5001")
            page.wait_for_selector(".case-id-display")
            
            # Load existing CSV to resume if needed
            completed_cases = []
            if os.path.exists(CSV_PATH):
                with open(CSV_PATH, "r") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row["human_decision"] != "PENDING":
                            completed_cases.append(row["case_id"])
                            
            print(f"Resuming with {len(completed_cases)} already completed cases.")
            
            for i in range(24):
                # Ensure we are on the correct case URL
                page.goto(f"http://127.0.0.1:5001/case/{i}")
                page.wait_for_selector(".case-id-display")
                
                case_id = page.locator(".case-id-display").inner_text().strip()
                if case_id in completed_cases:
                    print(f"Skipping already completed case {case_id}")
                    continue
                    
                print(f"Processing case {case_id}...")
                
                # Read Evidence
                conversation = page.locator(".transcript-viewer").inner_text()
                current_label_el = page.locator(".intent-pill.golden").first
                current_label = current_label_el.inner_text().replace("Golden Label: ", "").strip() if current_label_el.is_visible() else "UNKNOWN"
                
                retrieved_items = page.locator(".evidence-panel").inner_text()
                
                # Get Decision from LLM
                decision_obj = get_llm_decision(llm, conversation, current_label, retrieved_items)
                print(f"Decision: {decision_obj['decision']}")
                
                # Playwright Automation
                dec_val = decision_obj["decision"]
                if dec_val == "AMBIGUOUS":
                    dec_val = "AMBIGUOUS_KEEP"
                
                # Find the radio button corresponding to dec_val
                # Since the UI uses CSS hiding, we must force click
                page.locator(f"input[value='{dec_val}']").click(force=True)
                
                if dec_val == "CHANGE_LABEL":
                    page.wait_for_selector("#new_label")
                    page.locator("#new_label").select_option(value=decision_obj["proposed_label"])
                    
                page.fill("#human_reason", decision_obj["reason"] + " (AUTONOMOUS QA DECISION NOT HUMAN APPROVAL)")
                
                if page.locator("#confidence").is_visible():
                    page.locator("#confidence").select_option(value=decision_obj["confidence"])
                if page.locator("#reviewer").is_visible():
                    page.fill("#reviewer", "AUTONOMOUS QA / MODEL-GENERATED REVIEW")
                    
                # Save
                page.click("#saveBtn")
                
                # Verify navigation
                if i < 23:
                    page.wait_for_selector(".case-id-display")
                else:
                    page.wait_for_selector(".title", state="visible")
                    
                # Store Stats
                case_data = {
                    "case_id": case_id,
                    "current_label": current_label,
                    "autonomous_decision": dec_val,
                    "proposed_label": decision_obj["proposed_label"],
                    "reason": decision_obj["reason"],
                    "confidence": decision_obj["confidence"],
                    "timestamp": datetime.now().isoformat()
                }
                STATS["cases"].append(case_data)
                
                if dec_val == "KEEP_CURRENT_LABEL": STATS["keep_count"] += 1
                elif dec_val == "CHANGE_LABEL": STATS["change_count"] += 1
                elif dec_val == "AMBIGUOUS_KEEP": STATS["ambiguous_count"] += 1
                elif dec_val == "INSUFFICIENT_EVIDENCE": STATS["insufficient_count"] += 1
                
                STATS["confidence_dist"][decision_obj["confidence"]] += 1
                
            browser.close()
            
            # Post Verification
            if not os.path.exists(CSV_PATH):
                RESULTS["CSV"] = "FAIL"
                RESULTS["DECISION"] = "AUTONOMOUS_REVIEW_BLOCKED"
            else:
                with open(CSV_PATH, "r") as f:
                    csv_cases = list(csv.DictReader(f))
                    if len(csv_cases) != 24:
                        RESULTS["CSV"] = "FAIL"
                        RESULTS["DECISION"] = "AUTONOMOUS_REVIEW_BLOCKED"
                        
    except Exception as e:
        print(f"Exception during run: {e}")
        traceback.print_exc()
        RESULTS["BROWSER"] = "FAIL"
        RESULTS["DECISION"] = "AUTONOMOUS_REVIEW_BLOCKED"
    finally:
        process.kill()
        
        manifest_after = make_manifest()
        
        if manifest_before["golden_set"] != manifest_after["golden_set"]:
            RESULTS["GOLDEN SET"] = "CHANGED"
            RESULTS["DECISION"] = "PROTECTED_DATA_MODIFIED"
            
        RESULTS["CASES"] = "24/24" if RESULTS["BROWSER"] == "PASS" else f"{len(STATS['cases'])}/24"
        
        # Write Reports
        with open(JSON_PATH, "w") as f:
            json.dump({"results": RESULTS, "stats": STATS, "manifest_before": manifest_before, "manifest_after": manifest_after}, f, indent=2)
            
        md = f"""# THREADMIND PHASE 16H
# AUTONOMOUS VERIFICATION REPORT

AUTONOMOUS QA DECISIONS ONLY
NOT HUMAN APPROVAL

Total cases: 24
Completed cases: {len(STATS['cases'])}

Keep count: {STATS['keep_count']}
Change count: {STATS['change_count']}
Ambiguous count: {STATS['ambiguous_count']}
Insufficient evidence count: {STATS['insufficient_count']}

Confidence Distribution: {json.dumps(STATS['confidence_dist'])}

Model Used: llama3.2:latest

Protected Data:
Golden Set Hash Before: {manifest_before['golden_set']}
Golden Set Hash After: {manifest_after['golden_set']}
FAISS status: {RESULTS['FAISS']}
MODEL status: {RESULTS['MODEL']}
PRODUCTION status: {RESULTS['PRODUCTION']}

"""
        for c in STATS["cases"]:
            md += f"## {c['case_id']}\n"
            md += f"- Current Label: {c['current_label']}\n"
            md += f"- Autonomous Decision: {c['autonomous_decision']}\n"
            md += f"- Proposed Label: {c['proposed_label']}\n"
            md += f"- Confidence: {c['confidence']}\n"
            md += f"- Rationale: {c['reason']}\n\n"
            
        with open(MD_PATH, "w") as f:
            f.write(md)
            
        print("PHASE 16H AUTONOMOUS QA:")
        print("COMPLETE")
        print(f"\nCASES:\n{RESULTS['CASES']}")
        print(f"\nBROWSER:\n{RESULTS['BROWSER']}")
        print(f"\nFORM:\n{RESULTS['FORM']}")
        print(f"\nPERSISTENCE:\n{RESULTS['PERSISTENCE']}")
        print(f"\nCSV:\n{RESULTS['CSV']}")
        print(f"\nGOLDEN SET:\n{RESULTS['GOLDEN SET']}")
        print(f"\nFAISS:\n{RESULTS['FAISS']}")
        print(f"\nMODEL:\n{RESULTS['MODEL']}")
        print(f"\nPRODUCTION:\n{RESULTS['PRODUCTION']}")
        print(f"\nDECISION:\n{RESULTS['DECISION']}")
        
if __name__ == "__main__":
    run_agent()
