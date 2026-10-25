"""Запустить собственные входы через CLI и сохранить проверяемый RESULTS.md."""

import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = Path("examples/task_1_1")
RESULTS = Path("results/task_1_1")


def execute(args: list[str], expected: int = 0) -> subprocess.CompletedProcess:
    result = subprocess.run([sys.executable, "main.py", *args], cwd=ROOT,
                            capture_output=True, text=True, timeout=60)
    if result.returncode != expected:
        raise RuntimeError(f"CLI {args}: код {result.returncode}, stderr={result.stderr}")
    return result


def main() -> None:
    (ROOT / RESULTS).mkdir(parents=True, exist_ok=True)
    lines = [
        "# Результаты задачи 1.1", "", "Вариант s=2. Seed=2.", "",
        f"Проверенная версия Python: {platform.python_version()}.", "",
        "Воспроизведение: `python3 tools/record_results.py`.",
        "Полные JSON-выводы и реализации лежат в `results/task_1_1/`.", "",
    ]
    variant = execute(["--variant"])
    lines += ["## Параметры", "", "```json", variant.stdout.rstrip(), "```", ""]
    table = []
    for name in ["iid", "periodic", "markov", "nonergodic", "deterministic"]:
        source = str(EXAMPLES / f"{name}.json")
        generated = execute(["generate", source, "--n", "20", "--seed", "2"])
        (ROOT / RESULTS / f"{name}_sample.jsonl").write_text(generated.stdout, encoding="utf-8")
        word = ["A", "A"] if name == "deterministic" else ["A", "B"]
        args = ["analyze", source, "--n", "1000000", "--word", *word, "--seed", "2"]
        measured = execute(args)
        (ROOT / RESULTS / f"{name}.json").write_text(measured.stdout, encoding="utf-8")
        data = json.loads(measured.stdout)
        table.append(f"| {name} | {''.join(word)} | {data['exact_first']['fraction']} | "
                     f"{data['exact_period_average']['fraction']} | {data['frequency']['decimal']:.9f} |")
        lines += [f"## {name}", "", f"Команда: `python3 main.py {' '.join(args)}`", "",
                  "Первые 20 символов (`generate`, те же seed и источник):", "",
                  "```text", " ".join(json.loads(line) for line in generated.stdout.splitlines()), "```", "",
                  "| N | Частота | Отклонение от первого такта | Отклонение от среднего |",
                  "|---:|---:|---:|---:|"]
        for row in data["table"]:
            lines.append(f"| {row['N']} | {row['frequency']['decimal']:.9f} | "
                         f"{row['error_first']['decimal']:.9f} | {row['error_period_average']['decimal']:.9f} |")
        lines += [""]
    summary = ["| Источник | Блок | P на первом такте | Среднее по L | Частота при N=10⁶ |",
               "|---|---|---:|---:|---:|", *table]
    lines += ["## Сводная таблица", "", *summary, "", "## Некорректные входы", ""]
    for path in sorted((ROOT / EXAMPLES / "invalid").glob("*.json")):
        for mode, args in [("generate", ["--n", "1"]),
                           ("analyze", ["--n", "100", "--word", "A"])]:
            result = execute([mode, str(path.relative_to(ROOT)), *args], expected=2)
            lines += [f"- `{mode} {path.name}` → код 2; `{result.stderr.strip()}`"]
    target = ROOT / "RESULTS.md"
    marker = "# Результаты задачи 1.2"
    previous = target.read_text(encoding="utf-8") if target.exists() else ""
    following = marker + previous.split(marker, 1)[1] if marker in previous else ""
    target.write_text("\n".join(lines) + "\n" + ("\n" + following if following else ""), encoding="utf-8")
    (ROOT / RESULTS / "summary.txt").write_text("\n".join(summary) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
