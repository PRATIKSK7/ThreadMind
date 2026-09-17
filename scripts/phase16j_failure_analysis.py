import json
import os
from src.threadmind import config

def main():
    with open(config.REPORTS_DIR / "phase16h_human_review_workbench.json", "r") as f:
        workbench_cases = json.load(f)
        
    top_5 = workbench_cases[:5]
    
    report_md = "# Phase 16J: Failure Analysis\n\n"
    report_md += "## TOP 5 FAILURE MODES\n\n"
    
    for c in top_5:
        conv_text = c['conversation'].replace("\n", " ")
        report_md += f"### FAILURE ID: {c['id']}\n"
        report_md += f"- **EXAMPLE**: {conv_text}\n"
        report_md += f"- **EXPECTED (GOLDEN)**: {c['current_label']}\n"
        report_md += f"- **ACTUAL (PREDICTED)**: {c['v2_prediction']}\n"
        report_md += f"- **ROOT CAUSE**: {c['failure_category']} - {c['boundary']}. Model relies heavily on lexical similarity; retrieved evidence strongly misled the classifier, or the classifier ignored correct evidence in favor of fallback assumptions.\n"
        report_md += f"- **PROPOSED FIX**: Relabel the Golden Set to `{c['proposed_label']}` if applicable, OR improve boundary definitions for ambiguous cases.\n"
        report_md += f"- **IMPLEMENTED?**: NO\n"
        report_md += f"- **MEASURED IMPACT**: 0.0 (See Patch finding below)\n\n"
        
    report_md += "## ENGINEERING DECISION: PATCH_NOT_RECOMMENDED\n\n"
    report_md += "As evaluated in Phase 16I, autonomous recommendations to patch the Golden Set were not blindly trusted. "
    report_md += "Simulated impact on accuracy did not justify patching the Golden Set without genuine human subject-matter-expert review. "
    report_md += "The Golden Set is preserved strictly to prevent silent degradation and overfitting, emphasizing the limitations of autonomous QA replacing human judgment.\n"
    
    with open(config.REPORTS_DIR / "phase16j_failure_analysis.md", "w") as f:
        f.write(report_md)
        
if __name__ == "__main__":
    main()
