"""Реальные CLI-выводы задачи 1.2 и отдельный замер полного запуска при k=5."""

import json
from pathlib import Path
import platform
import subprocess
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = Path("results/task_1_2")
MARKER = "# Результаты задачи 1.2"
CASES = [
    ("below", "iid", "1"), ("above", "iid", "3/2"), ("full", "iid", "2"),
    ("at_entropy", "iid", "H"), ("uniform_boundary", "uniform", "H"),
    ("dyadic_boundary", "dyadic", "3/2"), ("small_n", "skewed", "0"),
    ("deterministic", "deterministic", "0"), ("hidden", "iid_hidden", "2"),
]


def execute(arguments, expected=0):
    """Запустить CLI с тайм-аутом и отвергнуть неожиданный код завершения."""
    result = subprocess.run([sys.executable, "main.py", *map(str, arguments)],
                            cwd=ROOT, text=True, capture_output=True, timeout=30)
    if result.returncode != expected:
        raise RuntimeError(f"{arguments}: код {result.returncode}, {result.stderr}")
    return result


def main():
    """Сохранить таблицы и коды задачи 1.2, диагностики и замер при k=5,n_max=50.

    Обновляется только раздел задачи 1.2 в RESULTS.md; JSON-файлы результатов
    перезаписываются, время измеряется отдельно от детерминированного вывода.
    """
    (ROOT / DIRECTORY).mkdir(parents=True, exist_ok=True)
    lines = [MARKER, "", "Вариант s=2, q=5, ε=1/10000, n_max=50.", "",
             f"Python {platform.python_version()}. `python3 tools/record_uniform_results.py`.", "",
             "Случайности в задаче 1.2 нет. Полные таблицы и описания кодов — `results/task_1_2/`.", ""]
    summary = ["| Вход | R | H, бит/символ | Первое n≤50 | P_e(50) | Условие выполнено для всех достаточно больших n |",
               "|---|---:|---:|---:|---:|---|"]
    for label, source, rate in CASES:
        source_path = Path(f"examples/task_1_2/{source}.json")
        information = execute(["entropy", source_path])
        (ROOT / DIRECTORY / f"{source}_entropy.json").write_text(information.stdout, encoding="utf-8")
        arguments = ["uniform", str(source_path), "--rate", rate, "--n-max", "50",
                     "--code-output", str(DIRECTORY / f"{label}_code.json")]
        output = execute(arguments)
        (ROOT / DIRECTORY / f"{label}.json").write_text(output.stdout, encoding="utf-8")
        data = json.loads(output.stdout)
        yes = "да" if data["asymptotic"]["eventually_below_epsilon"] else "нет"
        summary.append(f"| {source} | {rate} | {float(data['entropy_bits']):.9f} | "
                       f"{data['minimum_n'] if data['minimum_n'] is not None else '—'} | "
                       f"{data['table'][-1]['error']['decimal']:.9g} | {yes} |")
        lines += [f"## {label}", "", f"`python3 main.py {' '.join(arguments)}`", "",
                  f"Асимптотика: {data['asymptotic']['reason']}.", "",
                  "| n | ℓ | Число кодируемых блоков | P_e, точно | P_e, приближённо |",
                  "|---:|---:|---:|---:|---:|"]
        selected = {1, 2, 3, 4, 10, 11, 25, 50}
        if data["minimum_n"]:
            selected.add(data["minimum_n"])
        for row in data["table"]:
            if row["n"] in selected:
                lines.append(f"| {row['n']} | {row['length']} | {row['selected_blocks']} | "
                             f"{row['error']['fraction']} | {row['error']['decimal']:.9g} |")
        lines.append("")
    lines += ["## Сводная таблица", "", *summary, "", "## Диагностика", ""]
    for name in ["periodic", "markov", "nonergodic"]:
        for mode in ["entropy", "uniform"]:
            args = [mode, f"examples/task_1_1/{name}.json"]
            if mode == "uniform":
                args += ["--rate", "2", "--code-output", str(DIRECTORY / "rejected_code.json")]
            result = execute(args, expected=2)
            lines.append(f"- `{mode} {name}.json`: код 2, {result.stderr.strip()}")
    benchmark = ["uniform", "tests/fixtures/uniform_k5.json", "--rate", "1", "--n-max", "50",
                 "--code-output", str(DIRECTORY / "benchmark_code.json")]
    start = perf_counter()
    performance = execute(benchmark)
    seconds = perf_counter() - start
    (ROOT / DIRECTORY / "benchmark.json").write_text(performance.stdout, encoding="utf-8")
    timing = {"seconds": seconds, "python": platform.python_version(), "platform": platform.platform(),
              "command": [sys.executable, "main.py", *benchmark], "within_10_seconds": seconds <= 10}
    (ROOT / DIRECTORY / "timing.json").write_text(json.dumps(timing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines += ["", "## Производительность", "",
              f"Отдельный контрольный вход k=5, n_max=50: **{seconds:.3f} с** на Python {platform.python_version()}.",
              "Измерен полный CLI-процесс: чтение и проверка источника, 50 строк таблицы, сохранение кода и вывод JSON.",
              "Этот вход проверяет требование k≤5 и отличается от собственного варианта k=3.",
              "Подробности замера — `results/task_1_2/timing.json`. Время не включается в детерминированные результаты.", ""]
    results = ROOT / "RESULTS.md"
    previous = results.read_text(encoding="utf-8")
    first_part = previous.split(MARKER, 1)[0].rstrip()
    next_marker = "# Результаты задачи 1.3"
    following = next_marker + previous.split(next_marker, 1)[1] if next_marker in previous else ""
    results.write_text(first_part + "\n\n" + "\n".join(lines).rstrip() + "\n" +
                       ("\n" + following if following else ""), encoding="utf-8")
    (ROOT / DIRECTORY / "summary.txt").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(f"k=5, n_max=50: {seconds:.3f} с; лимит 10 с: {timing['within_10_seconds']}")


if __name__ == "__main__":
    main()
