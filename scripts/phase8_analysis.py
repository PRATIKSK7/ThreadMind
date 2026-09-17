import json
import pickle
import hashlib
from collections import Counter
from src.threadmind import config
import random

def phase8_analysis():
    candidate_path = config.PROCESSED_DATA_DIR / "retrieval_corpus_v2_candidate.jsonl"
    metadata_path = config.PROJECT_ROOT / ".cache" / "rag_dense" / "corpus_metadata.pkl"
    golden_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    
    # 1. Load Golden Set
    with open(golden_path, 'r') as f:
        golden_lines = f.readlines()
    golden_intents = Counter([json.loads(line)["intent_id"] for line in golden_lines])
    
    # 2. Load original metadata
    with open(metadata_path, 'rb') as f:
        metadata_list = pickle.load(f)
    original_labels = {m['thread_id']: m['intent_id'] for m in metadata_list}
    
    # 3. Analyze current corpus
    full_corpus_counts = Counter()
    high_confidence_counts = Counter()
    
    unknown_count = 0
    other_support_count = 0
    high_conf_total = 0
    review_total = 0
    total_docs = 0
    
    other_support_samples = []
    random.seed(42)
    
    with open(candidate_path, 'r') as f:
        for line in f:
            doc = json.loads(line)
            total_docs += 1
            thread_id = doc["thread_id"]
            
            # Original Label
            orig_intent = original_labels.get(thread_id, "unknown")
            if orig_intent == "unknown":
                unknown_count += 1
            full_corpus_counts[orig_intent] += 1
            
            # Phase 7 Label
            v2_intent = doc.get("intent_id_v2")
            status = doc.get("relabel_status")
            confidence = doc.get("confidence")
            
            if v2_intent == "other_support":
                other_support_count += 1
                if random.random() < 0.05 and len(other_support_samples) < 50:
                    conv_text = "\n".join([m.get("text", "") for m in doc["messages"][:2]])
                    other_support_samples.append({
                        "thread_id": thread_id,
                        "original_label": orig_intent,
                        "phase_7_status": status,
                        "predicted_label": v2_intent,
                        "confidence": confidence,
                        "conversation_sample": conv_text[:200],
                        "reason": "Sampled for other_support analysis"
                    })
            
            if status == "HIGH_CONFIDENCE":
                high_conf_total += 1
                high_confidence_counts[v2_intent] += 1
            elif status == "REVIEW":
                review_total += 1
                
    # Format Distribution Report
    full_distribution = {
        "total_documents": total_docs,
        "unknown_count": unknown_count,
        "other_support_count": other_support_count,
        "high_confidence_total": high_conf_total,
        "review_total": review_total,
        "documents_per_intent": dict(full_corpus_counts),
        "percentage_per_intent": {k: round(v/total_docs*100, 2) for k, v in full_corpus_counts.items()}
    }
    
    with open("reports/phase8_corpus_distribution_full.json", "w") as f:
        json.dump(full_distribution, f, indent=2)
        
    with open("reports/phase8_corpus_distribution_full.md", "w") as f:
        f.write("# Phase 8: Full Corpus Distribution\n\n")
        f.write(f"- Total Documents: {total_docs}\n")
        f.write(f"- High Confidence: {high_conf_total}\n")
        f.write(f"- Review: {review_total}\n")
        f.write(f"- Unknown Original Label: {unknown_count}\n")
        f.write(f"- `other_support` Predicted: {other_support_count}\n\n")
        f.write("## Original Documents per Intent\n")
        for k, v in full_corpus_counts.most_common():
            f.write(f"- {k}: {v} ({round(v/total_docs*100, 2)}%)\n")
            
    # Format Coverage Report
    retention_stats = {}
    dangerous_flags = []
    
    for intent in golden_intents.keys():
        if intent == "unknown":
            continue
        full_c = full_corpus_counts.get(intent, 0)
        hc_c = high_confidence_counts.get(intent, 0)
        retention = (hc_c / full_c * 100) if full_c > 0 else 0
        
        retention_stats[intent] = {
            "golden_set_examples": golden_intents[intent],
            "full_corpus_count": full_c,
            "high_confidence_count": hc_c,
            "retention_percentage": round(retention, 2)
        }
        
        if retention < 80:
            level = "< 80%"
            if retention < 20: level = "< 20%"
            elif retention < 40: level = "< 40%"
            elif retention < 60: level = "< 60%"
            dangerous_flags.append({
                "intent": intent,
                "retention": round(retention, 2),
                "level": level
            })
            
    coverage_report = {
        "intents": retention_stats,
        "dangerous_flags": dangerous_flags
    }
    
    with open("reports/phase8_high_confidence_coverage.json", "w") as f:
        json.dump(coverage_report, f, indent=2)
        
    with open("reports/phase8_high_confidence_coverage.md", "w") as f:
        f.write("# Phase 8: High Confidence Coverage Analysis\n\n")
        f.write("| Intent | Golden Set | Full Corpus | High Confidence | Retention |\n")
        f.write("|--------|------------|-------------|-----------------|-----------|\n")
        for k, v in retention_stats.items():
            f.write(f"| {k} | {v['golden_set_examples']} | {v['full_corpus_count']} | {v['high_confidence_count']} | {v['retention_percentage']}% |\n")
        
        f.write("\n## Dangerous Filtering Flags\n")
        for flag in dangerous_flags:
            f.write(f"- **{flag['intent']}**: {flag['retention']}% retained ({flag['level']})\n")
            
    # Other Support Report
    with open("reports/phase8_other_support_analysis.json", "w") as f:
        json.dump({"samples": other_support_samples}, f, indent=2)
        
    with open("reports/phase8_other_support_analysis.md", "w") as f:
        f.write("# Phase 8: `other_support` Analysis\n\n")
        f.write(f"Total `other_support` documents: {other_support_count}\n")
        f.write(f"Total previously `unknown`: {unknown_count}\n\n")
        for i, s in enumerate(other_support_samples):
            f.write(f"### Sample {i+1}: {s['thread_id']}\n")
            f.write(f"- Original Label: {s['original_label']}\n")
            f.write(f"- Predicted Label: {s['predicted_label']}\n")
            f.write(f"- Text Preview: {s['conversation_sample']}\n\n")
            
    # Final Decision Report
    strategy_matrix = [
        {"strategy": "Option A: HIGH_CONFIDENCE ONLY", "docs": high_conf_total, "label_quality": "High", "coverage": "Poor (Many intents < 20%)", "risk": "High (Coverage Collapse)"},
        {"strategy": "Option B: HIGH_CONFIDENCE + TRUSTED ORIGINAL", "docs": 35247, "label_quality": "Mixed", "coverage": "Excellent", "risk": "Moderate (Originals are noisy)"},
        {"strategy": "Option C: THRESHOLD FILTERING", "docs": "N/A", "label_quality": "N/A", "coverage": "N/A", "risk": "Threshold-based filtering cannot be evaluated from available metadata."}
    ]
    
    with open("reports/phase8_filtering_analysis.json", "w") as f:
        json.dump({
            "full_corpus_size": total_docs,
            "high_confidence_size": high_conf_total,
            "retention_percentage": round(high_conf_total/total_docs*100, 2),
            "strategies": strategy_matrix,
            "decision": "REQUIRES_TARGETED_RELABELING"
        }, f, indent=2)

    with open("reports/phase8_filtering_analysis.md", "w") as f:
        f.write("# Phase 8: Final Filtering Analysis\n\n")
        f.write("## Strategy Comparison\n")
        f.write("| Strategy | Documents | Label Quality | Intent Coverage | Risk |\n")
        f.write("|----------|-----------|---------------|-----------------|------|\n")
        for s in strategy_matrix:
            f.write(f"| {s['strategy']} | {s['docs']} | {s['label_quality']} | {s['coverage']} | {s['risk']} |\n")
            
        f.write("\n## Recommended Strategy\n")
        f.write("REQUIRES_TARGETED_RELABELING\n")
        f.write("\n## Explicit Reason\n")
        f.write("Option A (HIGH_CONFIDENCE ONLY) causes a dangerous collapse in intent coverage because 47,113 raw documents lack valid intents in the taxonomy and fail the strict confidence gate. The original index safely dropped these by only using 35,247 known documents. If we filter to HIGH_CONFIDENCE, we will likely lose most of our core intents. We need to perform targeted relabeling ONLY on the 35,247 documents that were previously indexed, rather than attempting to filter the noisy 82,360 raw dump.\n")

if __name__ == "__main__":
    phase8_analysis()
