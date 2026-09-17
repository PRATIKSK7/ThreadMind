import json
import random
from src.threadmind import config

DEFAULT_SEED = 42

def load_threads(filepath):
    threads = []
    with open(filepath, "r") as f:
        for line in f:
            threads.append(json.loads(line))
    return threads

def main():
    all_threads_path = config.PROCESSED_DATA_DIR / "AmazonHelp_threads.jsonl"
    golden_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    
    print(f"Loading {golden_path}...")
    golden_records = load_threads(golden_path)
    golden_ids = {r['thread_id'] for r in golden_records}
    
    print(f"Loading {all_threads_path}...")
    all_threads = load_threads(all_threads_path)
    
    # 1. Filter out golden threads completely
    pool = [th for th in all_threads if th['thread_id'] not in golden_ids]
    
    # 2. Shuffle deterministically
    random.seed(DEFAULT_SEED)
    random.shuffle(pool)
    
    # 3. Split 80/20
    split_index = int(len(pool) * 0.8)
    train_pool = pool[:split_index]
    val_pool = pool[split_index:]
    
    # Write to files
    train_path = config.PROCESSED_DATA_DIR / "train_split.jsonl"
    val_path = config.PROCESSED_DATA_DIR / "val_split.jsonl"
    
    with open(train_path, "w") as f:
        for r in train_pool:
            f.write(json.dumps(r) + "\n")
            
    with open(val_path, "w") as f:
        for r in val_pool:
            f.write(json.dumps(r) + "\n")
            
    # Leakage Audit
    train_ids = {th['thread_id'] for th in train_pool}
    val_ids = {th['thread_id'] for th in val_pool}
    
    golden_threads_in_training = len(golden_ids.intersection(train_ids))
    golden_threads_in_validation = len(golden_ids.intersection(val_ids))
    
    assert golden_threads_in_training == 0, "LEAKAGE: Golden threads found in training split."
    assert golden_threads_in_validation == 0, "LEAKAGE: Golden threads found in validation split."
    
    print("Leakage audit passed.")
    
    stats = {
        "golden_set_size": len(golden_ids),
        "total_available_pool": len(pool),
        "training_set_size": len(train_pool),
        "validation_set_size": len(val_pool),
        "golden_threads_in_training": golden_threads_in_training,
        "golden_threads_in_validation": golden_threads_in_validation
    }
    
    with open(config.REPORTS_DIR / "training_leakage_audit.json", "w") as f:
        json.dump(stats, f, indent=2)
        
    with open(config.REPORTS_DIR / "training_leakage_audit.md", "w") as f:
        f.write("# Training Leakage Audit\n\n")
        f.write(f"- **Golden Set Size**: {stats['golden_set_size']}\n")
        f.write(f"- **Training Set Size**: {stats['training_set_size']}\n")
        f.write(f"- **Validation Set Size**: {stats['validation_set_size']}\n")
        f.write(f"- **Golden Threads in Training**: {stats['golden_threads_in_training']}\n")
        f.write(f"- **Golden Threads in Validation**: {stats['golden_threads_in_validation']}\n\n")
        f.write("> [!NOTE]\n> The training and validation splits are 100% clean and contain zero thread IDs present in the Golden Set.\n")

if __name__ == "__main__":
    main()
