"""Tool Calling Basics experiment.

Tests native vs prompt-based tool calling across local models.
8 test cases × 4 models × 5 runs = 160 total runs.
"""

import json
from pathlib import Path

from rich.console import Console

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from harness import OllamaClient, TestCase, ResultCollector

console = Console()

MODELS = ["gpt-oss-20b", "glm-4.7-flash", "gpt-oss-120b", "nemotron-3-nano"]
RUNS_PER_TEST = 5

# Load tool definitions and prompt template
tools_path = Path(__file__).parent / "tools.json"
tools = json.loads(tools_path.read_text())
prompt_template_path = Path(__file__).parent / "prompt_template.txt"
prompt_template = prompt_template_path.read_text()

# Single tool (weather only)
single_tool = [tools[0]]

# All three tools (for selection tests)
all_tools = tools

# --- Test Cases ---

TESTS = [
    # Native tool calling
    TestCase(
        id="tc-01",
        name="Single tool, simple args",
        category="native",
        messages=[{"role": "user", "content": "What's the weather in Paris?"}],
        tools=single_tool,
        expected_tool="get_weather",
        expected_args={"location": "Paris"},
    ),
    TestCase(
        id="tc-02",
        name="Single tool, multiple args",
        category="native",
        messages=[{"role": "user", "content": "Search the web for 'latest AI news' and give me 3 results"}],
        tools=[tools[1]],
        expected_tool="search_web",
        expected_args={"query": "latest AI news", "num_results": 3},
    ),
    TestCase(
        id="tc-03",
        name="Tool selection (pick 1 from 3)",
        category="native",
        messages=[{"role": "user", "content": "What is 42 * 17?"}],
        tools=all_tools,
        expected_tool="calculate",
        expected_args={"expression": "42 * 17"},
    ),
    TestCase(
        id="tc-04",
        name="Parallel tool calls (3 cities)",
        category="native",
        messages=[{"role": "user", "content": "What's the weather in Paris, London, and Tokyo?"}],
        tools=single_tool,
        expected_tool="get_weather",
        expected_args={"location": "Paris"},  # Check at least the first call
    ),
    # Prompt-based tool calling
    TestCase(
        id="tc-05",
        name="Single tool, simple args",
        category="prompt-based",
        messages=[{"role": "user", "content": "What's the weather in Paris?"}],
        tools=single_tool,
        prompt_template=prompt_template,
        expected_tool="get_weather",
        expected_args={"location": "Paris"},
    ),
    TestCase(
        id="tc-06",
        name="Single tool, multiple args",
        category="prompt-based",
        messages=[{"role": "user", "content": "Search the web for 'latest AI news' and give me 3 results"}],
        tools=[tools[1]],
        prompt_template=prompt_template,
        expected_tool="search_web",
        expected_args={"query": "latest AI news", "num_results": 3},
    ),
    TestCase(
        id="tc-07",
        name="Tool selection (pick 1 from 3)",
        category="prompt-based",
        messages=[{"role": "user", "content": "What is 42 * 17?"}],
        tools=all_tools,
        prompt_template=prompt_template,
        expected_tool="calculate",
        expected_args={"expression": "42 * 17"},
    ),
    TestCase(
        id="tc-08",
        name="Parallel tool calls (3 cities)",
        category="prompt-based",
        messages=[{"role": "user", "content": "What's the weather in Paris, London, and Tokyo?"}],
        tools=single_tool,
        prompt_template=prompt_template,
        expected_tool="get_weather",
        expected_args={"location": "Paris"},
    ),
]


def main():
    client = OllamaClient()
    collector = ResultCollector("tool-calling-basics")

    total_runs = len(MODELS) * len(TESTS) * RUNS_PER_TEST
    console.print(f"\n[bold]Tool Calling Basics[/bold]")
    console.print(f"Models: {len(MODELS)}, Tests: {len(TESTS)}, Runs/test: {RUNS_PER_TEST}")
    console.print(f"Total runs: {total_runs}\n")

    run_count = 0
    for model in MODELS:
        console.print(f"\n[bold cyan]Model: {model}[/bold cyan]")
        for test in TESTS:
            for run in range(RUNS_PER_TEST):
                run_count += 1
                result = client.run_test(model, test, temperature=0)
                collector.add(model, test.id, run, result)
                status = "[green]PASS[/green]" if result.success else "[red]FAIL[/red]"
                console.print(
                    f"  [{run_count}/{total_runs}] {test.id} ({test.category}) "
                    f"run {run + 1}: {status} ({result.latency_ms:.0f}ms)"
                )

    console.print("\n")
    collector.print_summary()
    collector.export("results.json")


if __name__ == "__main__":
    main()
