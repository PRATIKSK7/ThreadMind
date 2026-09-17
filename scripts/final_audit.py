import os
import json
import hashlib
from src.threadmind import config

def main():
    print("Running Final Audit...")
    
    # 1. Check Golden Set Hash
    golden_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    with open(golden_path, "rb") as f:
        gs_hash = hashlib.sha256(f.read()).hexdigest()
    expected_hash = "6d4e700bfe65f0134acb39aa1ec0dbb1ba4dfafcf1ae1f0c102858ab2d54610f"
    assert gs_hash == expected_hash, f"Golden Set hash mismatch! Expected {expected_hash}, got {gs_hash}"
    print("[PASS] Golden Set Integrity Check")
    
    # 2. Check expected reports
    expected_reports = [
        "phase16e_taxonomy_audit.json",
        "phase16e_taxonomy_audit.md",
        "phase16h_human_decisions.csv",
        "phase16h_human_review_decisions.csv",
        "phase16h_human_review_workbench.json",
        "phase16j_baselines.md",
        "phase16j_baselines.json",
        "final_assignment_report.md"
    ]
    
    for report in expected_reports:
        path = config.REPORTS_DIR / report
        if not path.exists():
            print(f"[WARN] Missing required report: {report}")
        else:
            print(f"[PASS] Report exists: {report}")
        
    print("\nFINAL AUDIT CHECK COMPLETE.")
    
if __name__ == "__main__":
    main()
