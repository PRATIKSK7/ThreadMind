import json
import hashlib
from src.threadmind import config

def load_golden_set_ids(filepath):
    golden_ids = set()
    with open(filepath, "r") as f:
        for line in f:
            thread = json.loads(line)
            golden_ids.add(thread["thread_id"])
    return golden_ids

def build_retrieval_corpus():
    raw_path = config.PROCESSED_DATA_DIR / "AmazonHelp_threads.jsonl"
    golden_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    corpus_path = config.PROCESSED_DATA_DIR / "retrieval_corpus.jsonl"
    
    print(f"Loading golden set IDs from {golden_path}...")
    golden_ids = load_golden_set_ids(golden_path)
    print(f"Found {len(golden_ids)} golden threads to exclude.")
    
    print(f"Building retrieval corpus from {raw_path}...")
    corpus_count = 0
    with open(raw_path, "r") as infile, open(corpus_path, "w") as outfile:
        for line in infile:
            thread = json.loads(line)
            if thread["thread_id"] not in golden_ids:
                outfile.write(json.dumps(thread) + "\n")
                corpus_count += 1
                
    print(f"Successfully built retrieval corpus at {corpus_path} with {corpus_count} threads.")
    
    # Generate SHA-256 hash for reproducibility
    with open(corpus_path, "rb") as f:
        corpus_hash = hashlib.sha256(f.read()).hexdigest()
    print(f"Retrieval Corpus SHA-256: {corpus_hash}")

if __name__ == "__main__":
    build_retrieval_corpus()
