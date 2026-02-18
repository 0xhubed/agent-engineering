# Experiments

Experiment harness for testing agent patterns on local models via Ollama.

## Prerequisites

- Python 3.10+
- Ollama running locally (`http://localhost:11434`)
- Models pulled (see each experiment for required models)

## Setup

```bash
pip install -r requirements.txt
```

## Running an Experiment

```bash
cd tool-calling-basics
python run.py
```

Results are saved to `results.json` in the experiment directory.

## Exporting Results to Site

```bash
python export_results.py tool-calling-basics
```

This validates the results, copies them to `src/data/experiment-results/`, updates the experiment registry, and updates the model matrix.

## Structure

```
experiments/
  harness.py              # Shared: OllamaClient, TestCase, ResultCollector
  export_results.py       # Validate + copy results to src/data/
  requirements.txt        # Python dependencies
  <experiment-name>/
    run.py                # Defines test cases, runs experiment
    tools.json            # Tool definitions (if applicable)
    prompt_template.txt   # Prompt template (if applicable)
    results.json          # Output (gitignored)
```
