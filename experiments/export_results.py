"""Export experiment results to the site's data directory."""

import json
import sys
from pathlib import Path

SITE_DATA = Path(__file__).parent.parent / "src" / "data"
EXPERIMENTS_JSON = SITE_DATA / "experiments.json"
MODEL_MATRIX_JSON = SITE_DATA / "model-matrix.json"
RESULTS_DIR = SITE_DATA / "experiment-results"


def load_json(path: Path) -> dict | list:
    return json.loads(path.read_text())


def save_json(path: Path, data: dict | list) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n")


def export(experiment_id: str) -> None:
    """Validate and export results for an experiment."""
    experiment_dir = Path(__file__).parent / experiment_id
    results_file = experiment_dir / "results.json"

    if not results_file.exists():
        print(f"Error: {results_file} not found. Run the experiment first.")
        sys.exit(1)

    results = load_json(results_file)

    # Validate
    if results.get("experimentId") != experiment_id:
        print(f"Error: experimentId mismatch in {results_file}")
        sys.exit(1)

    if results.get("status") != "complete":
        print(f"Warning: experiment status is '{results.get('status')}', not 'complete'")

    if not results.get("results"):
        print("Error: no results found")
        sys.exit(1)

    # Copy to site data
    dest = RESULTS_DIR / f"{experiment_id}.json"
    save_json(dest, results)
    print(f"Copied results to {dest}")

    # Update experiments.json registry
    experiments = load_json(EXPERIMENTS_JSON)
    for exp in experiments:
        if exp["id"] == experiment_id:
            exp["status"] = "complete"
            break
    save_json(EXPERIMENTS_JSON, experiments)
    print(f"Updated {EXPERIMENTS_JSON}")

    # Update model-matrix.json
    matrix = load_json(MODEL_MATRIX_JSON)
    _update_matrix(matrix, experiment_id, results)
    save_json(MODEL_MATRIX_JSON, matrix)
    print(f"Updated {MODEL_MATRIX_JSON}")

    print("\nDone. Run 'npm run build' to rebuild the site.")


def _update_matrix(matrix: dict, experiment_id: str, results: dict) -> None:
    """Compute capability scores from results and update the matrix."""
    run_results = results.get("results", [])
    if not run_results:
        return

    # Group by model and compute overall success rate
    model_stats: dict[str, dict[str, int]] = {}
    for r in run_results:
        model = r["model"]
        if model not in model_stats:
            model_stats[model] = {"total": 0, "success": 0}
        model_stats[model]["total"] += 1
        if r.get("success"):
            model_stats[model]["success"] += 1

    scores = {}
    for model, stats in model_stats.items():
        score = round(100 * stats["success"] / stats["total"]) if stats["total"] > 0 else 0
        scores[model] = {"score": score, "runs": stats["total"]}

    # Remove existing entry for this experiment
    matrix["capabilities"] = [
        c for c in matrix.get("capabilities", [])
        if c.get("experimentId") != experiment_id
    ]

    # Add new entry
    matrix["capabilities"].append({
        "name": f"Tool Calling ({experiment_id})",
        "experimentId": experiment_id,
        "scores": scores,
    })

    matrix["lastUpdated"] = results.get("runDate")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python export_results.py <experiment-id>")
        sys.exit(1)
    export(sys.argv[1])
