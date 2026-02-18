"""Experiment harness for testing agent patterns on local models via Ollama."""

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import ollama
from pydantic import BaseModel
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()


class TestCase(BaseModel):
    """A single test case for an experiment."""
    id: str
    name: str
    category: str  # "native" or "prompt-based"
    messages: list[dict[str, str]]
    tools: list[dict[str, Any]] | None = None
    prompt_template: str | None = None
    expected_tool: str
    expected_args: dict[str, Any]


class RunResult(BaseModel):
    """Result of a single test run."""
    model: str
    test_id: str
    run_number: int
    success: bool
    tool_called: str | None = None
    args_returned: dict[str, Any] | None = None
    arg_correct: bool = False
    tool_selection_correct: bool | None = None
    latency_ms: float = 0
    input_tokens: int = 0
    output_tokens: int = 0
    raw_response: str = ""
    error: str | None = None


class OllamaClient:
    """Client for running test cases against Ollama models."""

    def __init__(self, host: str = "http://localhost:11434"):
        self.client = ollama.Client(host=host)

    def run_test(self, model: str, test: TestCase, temperature: float = 0) -> RunResult:
        """Run a single test case against a model."""
        start = time.perf_counter()

        try:
            if test.category == "native" and test.tools:
                return self._run_native(model, test, temperature, start)
            else:
                return self._run_prompt_based(model, test, temperature, start)
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            return RunResult(
                model=model,
                test_id=test.id,
                run_number=0,
                success=False,
                latency_ms=elapsed,
                error=str(e),
            )

    def _run_native(self, model: str, test: TestCase, temperature: float, start: float) -> RunResult:
        """Run using Ollama's native tool calling."""
        response = self.client.chat(
            model=model,
            messages=test.messages,
            tools=test.tools,
            options={"temperature": temperature},
        )
        elapsed = (time.perf_counter() - start) * 1000

        tool_calls = response.message.tool_calls or []
        if not tool_calls:
            return RunResult(
                model=model,
                test_id=test.id,
                run_number=0,
                success=False,
                latency_ms=elapsed,
                raw_response=response.message.content or "",
                error="No tool call in response",
            )

        first_call = tool_calls[0]
        tool_name = first_call.function.name
        tool_args = first_call.function.arguments

        arg_correct = self._check_args(tool_args, test.expected_args)
        tool_correct = tool_name == test.expected_tool

        return RunResult(
            model=model,
            test_id=test.id,
            run_number=0,
            success=tool_correct and arg_correct,
            tool_called=tool_name,
            args_returned=tool_args,
            arg_correct=arg_correct,
            tool_selection_correct=tool_correct,
            latency_ms=elapsed,
            input_tokens=response.prompt_eval_count or 0,
            output_tokens=response.eval_count or 0,
            raw_response=json.dumps({"tool_calls": [{"name": tool_name, "args": tool_args}]}),
        )

    def _run_prompt_based(self, model: str, test: TestCase, temperature: float, start: float) -> RunResult:
        """Run using prompt-based tool calling with XML parsing."""
        messages = list(test.messages)
        if test.prompt_template and test.tools:
            tool_defs = json.dumps(test.tools, indent=2)
            system_msg = test.prompt_template.replace("{tool_definitions}", tool_defs)
            messages.insert(0, {"role": "system", "content": system_msg})

        response = self.client.chat(
            model=model,
            messages=messages,
            options={"temperature": temperature},
        )
        elapsed = (time.perf_counter() - start) * 1000

        content = response.message.content or ""
        tool_name, tool_args = self._parse_tool_call_xml(content)

        if not tool_name:
            return RunResult(
                model=model,
                test_id=test.id,
                run_number=0,
                success=False,
                latency_ms=elapsed,
                raw_response=content,
                error="No <tool_call> found in response",
            )

        arg_correct = self._check_args(tool_args, test.expected_args) if tool_args else False
        tool_correct = tool_name == test.expected_tool

        return RunResult(
            model=model,
            test_id=test.id,
            run_number=0,
            success=tool_correct and arg_correct,
            tool_called=tool_name,
            args_returned=tool_args,
            arg_correct=arg_correct,
            tool_selection_correct=tool_correct,
            latency_ms=elapsed,
            input_tokens=response.prompt_eval_count or 0,
            output_tokens=response.eval_count or 0,
            raw_response=content,
        )

    @staticmethod
    def _parse_tool_call_xml(content: str) -> tuple[str | None, dict[str, Any] | None]:
        """Parse <tool_call>{"name": ..., "arguments": ...}</tool_call> from response."""
        match = re.search(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", content, re.DOTALL)
        if not match:
            return None, None
        try:
            data = json.loads(match.group(1))
            return data.get("name"), data.get("arguments", {})
        except json.JSONDecodeError:
            return None, None

    @staticmethod
    def _check_args(actual: dict[str, Any] | None, expected: dict[str, Any]) -> bool:
        """Check if actual args match expected (case-insensitive string values)."""
        if not actual:
            return False
        for key, value in expected.items():
            if key not in actual:
                return False
            actual_val = actual[key]
            if isinstance(value, str) and isinstance(actual_val, str):
                if actual_val.lower() != value.lower():
                    return False
            elif actual_val != value:
                return False
        return True


class ResultCollector:
    """Collects and exports experiment results."""

    def __init__(self, experiment_id: str):
        self.experiment_id = experiment_id
        self.results: list[RunResult] = []

    def add(self, model: str, test_id: str, run_number: int, result: RunResult) -> None:
        """Add a run result."""
        result.model = model
        result.test_id = test_id
        result.run_number = run_number
        self.results.append(result)

    def export(self, path: str = "results.json") -> None:
        """Export results to JSON."""
        data = {
            "experimentId": self.experiment_id,
            "status": "complete",
            "runDate": time.strftime("%Y-%m-%d"),
            "results": [r.model_dump() for r in self.results],
        }
        Path(path).write_text(json.dumps(data, indent=2))
        console.print(f"[green]Results exported to {path}[/green]")

    def print_summary(self) -> None:
        """Print a summary table of results."""
        table = Table(title=f"Results: {self.experiment_id}")
        table.add_column("Model")
        table.add_column("Test")
        table.add_column("Success Rate", justify="right")
        table.add_column("Avg Latency (ms)", justify="right")

        # Group by model + test
        groups: dict[tuple[str, str], list[RunResult]] = {}
        for r in self.results:
            key = (r.model, r.test_id)
            groups.setdefault(key, []).append(r)

        for (model, test_id), runs in sorted(groups.items()):
            successes = sum(1 for r in runs if r.success)
            avg_latency = sum(r.latency_ms for r in runs) / len(runs)
            table.add_row(
                model,
                test_id,
                f"{successes}/{len(runs)} ({100 * successes / len(runs):.0f}%)",
                f"{avg_latency:.0f}",
            )

        console.print(table)
