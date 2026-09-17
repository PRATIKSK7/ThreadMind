import sys
import json
import time
import os
from pathlib import Path
from src.threadmind import config
from src.threadmind.data import loader, audit

def main():
    start_time = time.time()
    print("Starting THREADMIND Data Audit...")
    
    # 1. Load data
    try:
        df = loader.load_twcs_dataset()
    except Exception as e:
        print(f"ERROR: Failed to load dataset: {e}")
        sys.exit(1)
        
    print("Dataset loaded successfully.")
    
    # 2. Audit Process
    audit_results = {}
    
    # A. Dataset dimensions
    audit_results["dataset"] = {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "memory_usage_mb": float(df.memory_usage(deep=True).sum() / (1024 * 1024))
    }
    
    audit_results["schema"] = list(df.columns)
    
    print("Auditing missing values...")
    audit_results["missing_values"] = audit.audit_missing_values(df)
    
    print("Auditing duplicates...")
    audit_results["duplicates"] = audit.audit_duplicates(df)
    
    print("Auditing text quality...")
    audit_results["text_quality"] = audit.audit_text_quality(df)
    
    print("Auditing inbound distribution...")
    audit_results["inbound_distribution"] = audit.audit_inbound_distribution(df)
    
    print("Auditing timestamps...")
    audit_results["timestamps"] = audit.audit_timestamps(df)
    
    print("Auditing response links...")
    audit_results["response_links"] = audit.audit_response_relationships(df)
    
    print("Analyzing thread statistics...")
    audit_results["thread_statistics"] = audit.analyze_thread_structure(df)
    
    print("Analyzing authors...")
    author_stats = audit.analyze_authors(df)
    candidates = audit.get_brand_candidates(author_stats)
    
    # Save artifacts
    print("Saving artifacts...")
    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save JSON
    with open(config.REPORTS_DIR / "data_audit.json", "w") as f:
        json.dump(audit_results, f, indent=2)
        
    # Save candidates CSV
    candidates.to_csv(config.REPORTS_DIR / "brand_candidates.csv", index=False)
    
    # Generate human-readable Markdown
    with open(config.REPORTS_DIR / "data_audit.md", "w") as f:
        f.write("# THREADMIND Data Audit\n\n")
        f.write("## Dataset Overview\n")
        f.write(f"- Rows: {audit_results['dataset']['rows']}\n")
        f.write(f"- Columns: {audit_results['dataset']['columns']}\n")
        f.write(f"- Memory Usage: {audit_results['dataset']['memory_usage_mb']:.2f} MB\n\n")
        
        f.write("## Warnings and Errors\n")
        # Generate warnings
        missing_text = audit_results['text_quality']['null_count']
        if missing_text > 0:
            f.write(f"- **WARNING**: Found {missing_text} rows with null text.\n")
            
        orphan_refs = audit_results['response_links']['in_response_to_tweet_id']['references_to_missing_ids']
        if orphan_refs > 0:
            f.write(f"- **WARNING**: Found {orphan_refs} orphan references (in_response_to_tweet_id points to a missing tweet).\n")
            
        invalid_times = audit_results['timestamps']['invalid_timestamps']
        if invalid_times > 0:
            f.write(f"- **ERROR**: Found {invalid_times} invalid timestamps.\n")
            
        dupes = audit_results['duplicates']['exact_rows']
        if dupes > 0:
            f.write(f"- **WARNING**: Found {dupes} exact duplicate rows.\n")
            
        f.write("\n## Candidates\n")
        f.write("Top 15 candidate brands exported to `brand_candidates.csv`.\n")

    end_time = time.time()
    print(f"Audit completed in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    main()
