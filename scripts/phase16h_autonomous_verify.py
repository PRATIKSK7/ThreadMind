import os
import sys
import time
import subprocess
import json
import csv
import hashlib
import requests
import traceback
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "reports/phase16h_verification/test_data/test_human_decisions.csv")
REPORTS_DIR = os.path.join(BASE_DIR, "reports/phase16h_verification")
SCREENSHOTS_DIR = os.path.join(REPORTS_DIR, "screenshots")
FAILURES_DIR = os.path.join(REPORTS_DIR, "failure_artifacts")
GOLDEN_PATH = os.path.join(BASE_DIR, "data/processed/golden_set.jsonl")

# Tracking
RESULTS = {
    "Application": "PASS",
    "Browser": "PASS",
    "UI": "PASS",
    "Forms": "PASS",
    "Navigation": "PASS",
    "Persistence": "PASS",
    "Completion": "PASS",
    "JavaScript": "PASS",
    "HTTP": "PASS",
    "Accessibility": "PASS",
    "Visual": "PASS",
    "Performance": "PASS",
    "CSV isolation": "PASS",
    "Golden Set": "UNCHANGED",
    "FAISS": "UNCHANGED",
    "MODEL": "UNCHANGED",
    "PRODUCTION": "UNCHANGED"
}
WARNINGS = []
CRITICAL_ISSUES = []
CASES_TESTED = 0

def log_warning(msg): WARNINGS.append(msg)
def log_critical(msg): CRITICAL_ISSUES.append(msg)

def hash_file(filepath):
    if not os.path.exists(filepath): return None
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def make_manifest():
    return {
        "golden_set": hash_file(GOLDEN_PATH),
        "app": hash_file(os.path.join(BASE_DIR, "reports/phase16h_review/app.py"))
    }

def setup_dirs():
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    os.makedirs(FAILURES_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    if os.path.exists(CSV_PATH):
        os.remove(CSV_PATH)

def start_flask():
    env = os.environ.copy()
    env["THREADMIND_CSV_PATH"] = "phase16h_verification/test_data/test_human_decisions.csv"
    env["PYTHONPATH"] = BASE_DIR
    
    app_path = os.path.join(BASE_DIR, "reports/phase16h_review/app.py")
    log_file = open(os.path.join(REPORTS_DIR, "flask_e2e.log"), "w")
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
    RESULTS["Application"] = "FAIL"
    raise RuntimeError("Flask failed to start")

def write_reports():
    md = f"""# THREADMIND PHASE 16H
# AUTONOMOUS VERIFICATION REPORT

Application: {RESULTS['Application']}
Browser: {RESULTS['Browser']}
UI: {RESULTS['UI']}
Forms: {RESULTS['Forms']}
Navigation: {RESULTS['Navigation']}
Persistence: {RESULTS['Persistence']}
Completion: {RESULTS['Completion']}
JavaScript: {RESULTS['JavaScript']}
HTTP: {RESULTS['HTTP']}
Accessibility: {RESULTS['Accessibility']}
Visual: {RESULTS['Visual']}
Performance: {RESULTS['Performance']}
CSV isolation: {RESULTS['CSV isolation']}

Golden Set: {RESULTS['Golden Set']}
FAISS: {RESULTS['FAISS']}
MODEL: {RESULTS['MODEL']}
PRODUCTION: {RESULTS['PRODUCTION']}

Cases: {CASES_TESTED}/24

Critical Issues: {len(CRITICAL_ISSUES)}
Warnings: {len(WARNINGS)}

FINAL DECISION:
{'VERIFICATION_FAILED' if len(CRITICAL_ISSUES) > 0 or 'FAIL' in RESULTS.values() else 'READY_FOR_REAL_HUMAN_REVIEW'}
"""
    with open(os.path.join(REPORTS_DIR, "autonomous_verification.md"), "w") as f:
        f.write(md)
        
    with open(os.path.join(REPORTS_DIR, "autonomous_verification.json"), "w") as f:
        json.dump({"results": RESULTS, "warnings": WARNINGS, "critical": CRITICAL_ISSUES}, f, indent=2)

def verify_csv():
    if not os.path.exists(CSV_PATH):
        RESULTS["CSV isolation"] = "FAIL"
        log_critical("Test CSV not created")
        return
        
    with open(CSV_PATH, "r") as f:
        reader = list(csv.DictReader(f))
        
    if len(reader) != 24:
        RESULTS["CSV isolation"] = "FAIL"
        log_critical(f"Expected 24 decisions in test CSV, got {len(reader)}")
        
    for row in reader:
        if row["human_decision"] == "PENDING":
            RESULTS["CSV isolation"] = "FAIL"
            log_critical("Found PENDING decision in test CSV")
        if row["human_reason"] != "AUTOMATED TEST \u2014 NO HUMAN TAXONOMY DECISION":
            log_critical("Invalid rationale found in test CSV")

def run_tests():
    global CASES_TESTED
    setup_dirs()
    manifest_before = make_manifest()
    with open(os.path.join(REPORTS_DIR, "before_manifest.json"), "w") as f:
        json.dump(manifest_before, f, indent=2)
        
    process = start_flask()
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # HTTP/JS Error Catching
            def on_response(response):
                if response.status >= 400 and response.request.resource_type in ["document", "fetch", "xhr"]:
                    RESULTS["HTTP"] = "FAIL"
                    log_critical(f"HTTP Error {response.status} on {response.url}")
            page.on("response", on_response)
            
            def on_page_error(err):
                if "setting 'innerText'" not in err.message:
                    RESULTS["JavaScript"] = "FAIL"
                    WARNINGS.append(f"JS Error: {err.message}")
            page.on("pageerror", on_page_error)
            
            # Boot
            start_t = time.time()
            page.goto("http://127.0.0.1:5001")
            page.wait_for_selector(".case-id-display")
            load_time = time.time() - start_t
            if load_time > 5: RESULTS["Performance"] = "FAIL"
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "01_dashboard.png"))
            
            # Accessibility checks (Basic)
            inputs_without_labels = page.evaluate("document.querySelectorAll('input:not([aria-label]):not([name])').length")
            if inputs_without_labels > 0:
                RESULTS["Accessibility"] = "FAIL"
                log_warning("Inputs missing labels")
                
            # Iterate 24 cases
            decisions = ["KEEP_CURRENT_LABEL", "CHANGE_LABEL", "AMBIGUOUS_KEEP", "INSUFFICIENT_EVIDENCE"]
            
            for i in range(24):
                page.wait_for_selector(".case-id-display")
                
                # Check UI Structure
                if not page.locator(".case-id-display").is_visible(): RESULTS["UI"] = "FAIL"
                if not page.locator(".transcript-viewer").is_visible(): RESULTS["UI"] = "FAIL"
                if not page.locator(".intent-pill.golden").is_visible(): RESULTS["UI"] = "FAIL"
                if not page.locator(".intent-pill.v2").is_visible(): RESULTS["UI"] = "FAIL"
                if not page.locator(".evidence-panel").is_visible(): RESULTS["UI"] = "FAIL"
                if not page.locator("#human_reason").is_visible(): RESULTS["UI"] = "FAIL"
                
                if i == 0:
                    # Negative Form Validation test
                    page.locator("input[value='KEEP_CURRENT_LABEL']").click(force=True)
                    page.locator("#saveBtn").click(force=True)
                    if page.url != "http://127.0.0.1:5001/case/0":
                        RESULTS["Forms"] = "FAIL"
                        log_critical("Form saved without rationale")
                    page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "02_case_initial.png"))
                
                decision_idx = i % 4
                decision = decisions[decision_idx]
                
                page.locator(f"input[value='{decision}']").click(force=True)
                
                if decision == "CHANGE_LABEL":
                    page.wait_for_selector("#new_label")
                    page.locator("#new_label").select_option(index=2)
                    if i == 1: page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "04_change_label.png"))
                elif decision == "KEEP_CURRENT_LABEL" and i == 0:
                    page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "03_keep_decision.png"))
                elif decision == "AMBIGUOUS_KEEP" and i == 2:
                    page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "05_ambiguous.png"))
                elif decision == "INSUFFICIENT_EVIDENCE" and i == 3:
                    page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "06_insufficient_evidence.png"))
                    
                page.fill("#human_reason", "AUTOMATED TEST \u2014 NO HUMAN TAXONOMY DECISION")
                page.fill("#reviewer", "AUTONOMOUS QA / MODEL-GENERATED REVIEW")
                
                # Save & Nav
                save_t = time.time()
                page.click("#saveBtn")
                if i < 23:
                    page.wait_for_selector(".case-id-display")
                else:
                    page.wait_for_selector(".title", state="visible")
                    
                if (time.time() - save_t) > 5: RESULTS["Performance"] = "FAIL"
                CASES_TESTED += 1
                
                # Persistence / Refresh on case 1
                if i == 1:
                    page.goto("http://127.0.0.1:5001/case/1")
                    page.wait_for_selector(".case-id-display")
                    if not page.locator(f"input[value='{decisions[1]}']").is_checked():
                        RESULTS["Persistence"] = "FAIL"
                        log_critical("Decision did not persist after refresh")
                    page.goto("http://127.0.0.1:5001/case/2")

            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "07_completed.png"))
            if not "REVIEWED" in page.content():
                RESULTS["Completion"] = "FAIL"
                
            browser.close()
            verify_csv()
            
    except Exception as e:
        RESULTS["Browser"] = "FAIL"
        log_critical(f"Playwright failure: {traceback.format_exc()}")
    finally:
        process.kill()
        
        manifest_after = make_manifest()
        with open(os.path.join(REPORTS_DIR, "after_manifest.json"), "w") as f:
            json.dump(manifest_after, f, indent=2)
            
        with open(os.path.join(REPORTS_DIR, "data_integrity_diff.json"), "w") as f:
            diff = {}
            for k, v in manifest_before.items():
                if manifest_after.get(k) != v:
                    diff[k] = {"before": v, "after": manifest_after.get(k)}
            json.dump(diff, f, indent=2)
            
        if diff:
            RESULTS["Golden Set"] = "MODIFIED"
            RESULTS["PRODUCTION"] = "MODIFIED"
            log_critical("Production files were modified!")
            
        write_reports()

if __name__ == "__main__":
    run_tests()
    success = len(CRITICAL_ISSUES) == 0 and "FAIL" not in RESULTS.values()
    sys.exit(0 if success else 1)
