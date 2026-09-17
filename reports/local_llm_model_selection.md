# Local LLM Model Selection Report

## Constraints
* **Hardware**: Apple Silicon (arm64)
* **RAM**: 8 GB Total
* **Requirement**: Reliable structured JSON generation, instruction following.

## Candidate Models Considered

| Model Name | Size | Approx. RAM Required (4-bit quantization) | Assessment |
| --- | --- | --- | --- |
| Llama 3 (8B) | 8B | ~4.7 GB | High capability, but leaves very little headroom for OS (MacOS uses ~2-3GB) and Python runtime. High risk of swap/OOM. |
| Mistral v0.3 (7B) | 7B | ~4.1 GB | Same issue as Llama 3 8B. Too close to RAM limits. |
| Phi-3-Mini | 3.8B | ~2.3 GB | Excellent reasoning, low footprint. |
| Qwen 2.5 (3B) | 3B | ~2.0 GB | Very good instruction following and JSON support. |
| Llama 3.2 (3B) | 3B | ~2.0 GB | State of the art small model. Native JSON mode support in Ollama. Excellent instruction following. |
| Llama 3.2 (1B) | 1B | ~0.7 GB | Extremely lightweight, but might lack complex reasoning for nuanced intent classification. |

## Selected Model
**`llama3.2` (3B parameters, default tag in Ollama)**

### Justification for 8 GB Apple Silicon
At 3 billion parameters with standard 4-bit quantization, Llama 3.2 requires approximately 2.0 GB to 2.5 GB of RAM. This leaves ~5.5 GB of RAM free for macOS operations, the Python evaluation scripts, and other background tasks, ensuring the system will not experience memory pressure, swapping, or OOM crashes during evaluation. It strikes the perfect balance between high-quality instruction following (crucial for zero-shot classification and structured JSON output) and hardware constraints.

### Quality Tradeoffs
While a 3B model is smaller than the standard 7B/8B models (or GPT-3.5), Llama 3.2 is highly optimized for tool use and structured output. There may be a slight drop in accuracy on the hardest, most ambiguous examples compared to an 8B model, but the deterministic JSON structure and the elimination of memory crashes heavily outweigh this tradeoff.

## Installation Instructions

Ollama is not pre-installed on this machine. To set up the environment:

```bash
# 1. Install Ollama via Homebrew
brew install --cask ollama

# 2. Start Ollama server (in a separate terminal or as a service)
# brew services start ollama

# 3. Pull the specific model
ollama pull llama3.2
```
