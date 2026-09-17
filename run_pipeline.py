import sys
import subprocess
from src.threadmind import config

def run_script(script_name, description):
    print(f"\n==================================================")
    print(f"RUNNING: {description}")
    print(f"SCRIPT: {script_name}")
    print(f"==================================================\n")
    
    result = subprocess.run([sys.executable, f"scripts/{script_name}"])
    if result.returncode != 0:
        print(f"\nError: {script_name} failed with exit code {result.returncode}", file=sys.stderr)
        sys.exit(1)

def main():
    # Verify expected project directories exist
    expected_dirs = [
        config.DATA_DIR,
        config.RAW_DATA_DIR,
        config.PROCESSED_DATA_DIR,
        config.EXPERIMENTS_DIR,
        config.REPORTS_DIR,
    ]
    
    missing_dirs = [d for d in expected_dirs if not d.exists()]
    if missing_dirs:
        print("Error: The following required directories are missing:", file=sys.stderr)
        for d in missing_dirs:
            print(f"  - {d}", file=sys.stderr)
        sys.exit(1)

    print("THREADMIND: Final End-to-End Evaluation Pipeline")
    print("This pipeline reproduces the final results of the customer support agent.")
    
    # 1. Router Evaluation
    run_script("evaluate_router_baseline.py", "Evaluating Fallback Router on Golden Set (Accuracy)")
    
    # 2. Validation Fallback Rate
    run_script("evaluate_router_validation_fast.py", "Evaluating Router Fallback Rate on 500 Unseen Threads")
    
    # 3. Reply Generation
    run_script("generate_replies.py", "Generating Grounded Replies using LLM")
    
    # 4. LLM-as-Judge Evaluation
    run_script("evaluate_generation_judge.py", "Evaluating Generated Replies with LLM-as-Judge")
    
    print("\n==================================================")
    print("PIPELINE COMPLETE.")
    print("All reports and generated data are available in the 'reports/' directory.")
    print("==================================================")

if __name__ == "__main__":
    main()
