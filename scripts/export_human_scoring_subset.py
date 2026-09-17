import json
import random
import csv
from src.threadmind import config

def main():
    replies_path = config.REPORTS_DIR / "generated_replies.json"
    if not replies_path.exists():
        print(f"Error: {replies_path} not found. Run generate_replies.py first.")
        return
        
    with open(replies_path, "r") as f:
        replies = json.load(f)
        
    # Sample 30 random replies
    random.seed(42)  # For reproducibility
    sampled = random.sample(replies, min(30, len(replies)))
    
    golden_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    golden_dict = {}
    with open(golden_path, "r") as f:
        for line in f:
            r = json.loads(line)
            golden_dict[r['example_id']] = r['conversation']
            
    output_path = config.REPORTS_DIR / "human_scoring_subset.csv"
    
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "example_id", 
            "conversation_history", 
            "agent_reply", 
            "human_correctness_1_to_5", 
            "human_groundedness_1_to_5", 
            "human_helpfulness_1_to_5", 
            "human_tone_1_to_5"
        ])
        
        for rep in sampled:
            conv = golden_dict[rep['example_id']]
            conv_lines = []
            for m in conv:
                role = "Customer" if m.get('inbound', True) else "Agent"
                conv_lines.append(f"{role}: {m.get('text', '')}")
            conv_str = "\n".join(conv_lines)
            
            writer.writerow([
                rep['example_id'],
                conv_str,
                rep['generated_reply'],
                "", "", "", ""  # Empty columns for the human to fill in
            ])
            
    print(f"Exported {len(sampled)} examples to {output_path}")
    print("INSTRUCTIONS FOR HUMAN ANNOTATOR:")
    print("1. Open the CSV file.")
    print("2. Read the conversation history and the agent reply.")
    print("3. Score Correctness, Groundedness, Helpfulness, and Tone from 1 to 5.")
    print("4. Save the file. Once human labels are available, we can run Judge-vs-Human agreement (Cohen's Kappa).")

if __name__ == "__main__":
    main()
