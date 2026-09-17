import os
import time
import subprocess
import shutil
import json
import csv
import hashlib
import requests
import sys
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "reports/phase16h_human_review_decisions.csv")
BACKUP_PATH = os.path.join(BASE_DIR, "reports/phase16h_human_review_decisions.csv.e2e_backup")
REPORTS_DIR = os.path.join(BASE_DIR, "reports/phase16h_verification")
SCREENSHOTS_DIR = os.path.join(REPORTS_DIR, "screenshots")
FAILURES_DIR = os.path.join(REPORTS_DIR, "failure_artifacts")
GOLDEN_PATH = os.path.join(BASE_DIR, "data/processed/golden_set.jsonl")

def setup_dirs():
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    os.makedirs(FAILURES_DIR, exist_ok=True)

def hash_file(filepath):
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def backup_csv():
    if os.path.exists(CSV_PATH):
        shutil.copy2(CSV_PATH, BACKUP_PATH)
        
    # Reset CSV to PENDING
    cases = []
    workbench_json_path = os.path.join(BASE_DIR, "reports/phase16h_human_review_workbench.json")
    with open(workbench_json_path, "r") as f:
        data = json.load(f)
        for c in data:
            cases.append({
                "case_id": c["id"],
                "current_label": c["current_label"],
                "proposed_label": "",
                "human_decision": "PENDING",
                "human_reason": "",
                "confidence": "",
                "reviewer": "",
                "timestamp": ""
            })
            
    headers = ["case_id", "current_label", "proposed_label", "human_decision", "human_reason", "confidence", "reviewer", "timestamp"]
    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(cases)

def restore_csv():
    if os.path.exists(BACKUP_PATH):
        shutil.copy2(BACKUP_PATH, CSV_PATH)
        os.remove(BACKUP_PATH)

def start_flask():
    env = os.environ.copy()
    env["REVIEWER"] = "E2E_TEST"
    env["THREADMIND_CSV_PATH"] = "phase16h_human_review_decisions.csv"
    env["PYTHONPATH"] = BASE_DIR
    
    app_path = os.path.join(BASE_DIR, "reports/phase16h_review/app.py")
    log_file = open(os.path.join(REPORTS_DIR, "flask_e2e.log"), "w")
    process = subprocess.Popen([sys.executable, app_path], env=env, stdout=log_file, stderr=subprocess.STDOUT)
    
    # Wait for server
    for _ in range(10):
        try:
            r = requests.get("http://127.0.0.1:5001/case/0")
            if r.status_code == 200:
                return process
            else:
                print(f"Waiting for Flask... got status {r.status_code}")
                time.sleep(1)
        except requests.exceptions.ConnectionError:
            time.sleep(1)
            
    process.kill()
    if 'r' in locals():
        print(r.text)
    raise RuntimeError("Flask failed to start")

import sys

def verify_csv():
    with open(CSV_PATH, "r") as f:
        reader = list(csv.DictReader(f))
        
    assert len(reader) == 24, f"Expected 24 decisions, got {len(reader)}"
    for row in reader:
        assert row["human_decision"] != "PENDING", f"Found PENDING decision in E2E output for {row['case_id']}"
        assert row["reviewer"] == "E2E_TEST", f"Invalid reviewer: {row['reviewer']}"
        assert row["human_reason"] != "", "Missing rationale"
        if row["human_decision"] == "CHANGE_LABEL":
            assert row["proposed_label"] != "", "CHANGE_LABEL requires proposed_label"
            
    with open(os.path.join(REPORTS_DIR, "e2e_decision_validation.json"), "w") as f:
        json.dump({"status": "PASS", "decisions": reader}, f, indent=2)

def run_e2e():
    setup_dirs()
    hash_before = hash_file(GOLDEN_PATH)
    backup_csv()
    
    process = start_flask()
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Initial load
            page.goto("http://127.0.0.1:5001")
            page.wait_for_selector(".case-id-display")
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "01_initial.png"))
            
            # Perform negative test on case 0
            # Try to save without selecting anything (html5 validation should block it)
            # Actually, Playwright can evaluate form validity
            is_valid = page.evaluate("document.getElementById('decisionForm').checkValidity()")
            assert is_valid == False, "Form should be invalid initially"
            
            # Select KEEP
            page.locator("input[value='KEEP_CURRENT_LABEL']").click(force=True)
            is_valid_after_radio = page.evaluate("document.getElementById('decisionForm').checkValidity()")
            assert is_valid_after_radio == False, "Form should still be invalid due to missing reason"
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "validation_error.png"))
            
            decisions = ["KEEP_CURRENT_LABEL", "CHANGE_LABEL", "AMBIGUOUS_KEEP", "INSUFFICIENT_EVIDENCE"]
            
            for i in range(24):
                page.wait_for_selector(".case-id-display")
                
                # Check assertions
                assert page.locator(".case-id-display").is_visible(), "Case ID missing"
                assert page.locator(".transcript-viewer").is_visible(), "Conversation missing"
                assert page.locator(".intent-pill.golden").is_visible(), "Golden label missing"
                assert page.locator(".intent-pill.v2").is_visible(), "V2 classification missing"
                assert page.locator(".evidence-panel").is_visible(), "Retrieval info missing"
                assert page.locator("#human_reason").is_visible(), "Reason input missing"
                assert page.locator("#saveBtn").is_visible(), "Save button missing"
                
                decision_idx = i % 4
                decision = decisions[decision_idx]
                
                page.locator(f"input[value='{decision}']").click(force=True)
                
                if decision == "CHANGE_LABEL":
                    page.wait_for_selector("#new_label")
                    page.locator("#new_label").select_option(index=2) # Pick some valid intent
                    page.screenshot(path=os.path.join(SCREENSHOTS_DIR, f"change_label_case{i}.png"))
                elif decision == "AMBIGUOUS_KEEP":
                    page.screenshot(path=os.path.join(SCREENSHOTS_DIR, f"ambiguous_case{i}.png"))
                elif decision == "INSUFFICIENT_EVIDENCE":
                    page.screenshot(path=os.path.join(SCREENSHOTS_DIR, f"insufficient_evidence_case{i}.png"))
                    
                page.fill("#human_reason", f"E2E browser verification: {decision} workflow.")
                page.fill("#reviewer", "E2E_TEST")
                
                page.click("#saveBtn")
                
                if i < 23:
                    page.wait_for_selector(".case-id-display")
                else:
                    page.wait_for_selector(".title", state="visible")
                    page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "final_completion.png"))
                    
            verify_csv()
            
            with open(os.path.join(REPORTS_DIR, "e2e_verification.json"), "w") as f:
                json.dump({"status": "PASS"}, f)
                
    except Exception as e:
        print(f"E2E Test Failed: {e}")
        with open(os.path.join(REPORTS_DIR, "e2e_verification.json"), "w") as f:
            json.dump({"status": "FAIL", "error": str(e)}, f)
        raise
    finally:
        process.kill()
        restore_csv()
        hash_after = hash_file(GOLDEN_PATH)
        assert hash_before == hash_after, "Golden set modified!"

if __name__ == "__main__":
    run_e2e()
    print("E2E SUCCESS")
