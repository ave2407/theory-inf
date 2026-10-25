"""Неинтерактивные режимы ДЗ №1."""

import argparse
from itertools import islice
import json
from pathlib import Path
import sys

from theory_inf.distributions import InputError, fraction_text, probability
from theory_inf.experiment import analyze
from theory_inf.source import Source, read_json
from theory_inf.variant import VARIANT
from theory_inf.uniform import analyze_uniform, entropy, iid_distribution
from theory_inf.archive import compress, decompress


def length(value: str) -> int | None:
    if value.lower() == "none":
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Ожидается целое N или None") from exc


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Теория информации, ДЗ №1")
    result.add_argument("--variant", action="store_true", help="параметры собственного варианта")
    commands = result.add_subparsers(dest="command")
    generate = commands.add_parser("generate", help="реализация: один JSON-символ на строку")
    generate.add_argument("source", help="JSON-описание источника")
    generate.add_argument("--n", type=length, default=None, help="длина; N<=0 или None: до Ctrl+C")
    generate.add_argument("--seed", type=int, default=0)
    generate.add_argument("--output", help="файл вместо stdout; будет перезаписан")
    estimate = commands.add_parser("analyze", help="точные вероятности и частотные оценки")
    estimate.add_argument("source", help="JSON-описание источника")
    estimate.add_argument("--n", type=int, required=True)
    word = estimate.add_mutually_exclusive_group(required=True)
    word.add_argument("--word", nargs="+", help="символы блока, например A B A")
    word.add_argument("--word-file", help="JSON-массив символов")
    estimate.add_argument("--seed", type=int, default=0)
    estimate.add_argument("--output", help="JSON-результат вместо stdout; будет перезаписан")
    information = commands.add_parser("entropy", help="проверка iid-источника и энтропия")
    information.add_argument("source", help="JSON-описание источника")
    information.add_argument("--output", help="JSON-результат вместо stdout")
    uniform = commands.add_parser("uniform", help="оптимальное равномерное кодирование")
    uniform.add_argument("source", help="JSON-описание источника")
    uniform.add_argument("--rate", required=True, help="биты/символ: дробь, десятичное число или H")
    uniform.add_argument("--q", type=int, default=VARIANT.q)
    uniform.add_argument("--epsilon", default=str(VARIANT.epsilon))
    uniform.add_argument("--n-max", type=int, default=50)
    uniform.add_argument("--code-output", default="code.json", help="описание кода, по умолчанию code.json")
    uniform.add_argument("--output", help="таблица JSON вместо stdout")
    for name, help_text in [("compress", "двухпроходное сжатие файла в .zmh"),
                            ("decompress", "восстановление .zmh с проверкой CRC32")]:
        archive = commands.add_parser(name, help=help_text)
        archive.add_argument("source", help="путь к входному файлу")
        archive.add_argument("--output", help="выходной файл; существующий файл не перезаписывается")
        archive.add_argument("--stats", action="store_true", help="вывести статистику сжатия")
    return result


def json_text(value: dict) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    except ValueError as exc:
        raise InputError(f"Не удалось представить результат в JSON: {exc}") from exc


def check_output_paths(args: argparse.Namespace) -> None:
    """Проверить пути до открытия файлов на запись, чтобы не затереть вход."""
    inputs = [Path(args.source)]
    if args.command == "analyze" and args.word_file:
        inputs.append(Path(args.word_file))
    outputs = [Path(args.output)] if args.output else []
    if args.command == "uniform":
        outputs.append(Path(args.code_output))
    for i, output_path in enumerate(outputs):
        for other in [*inputs, *outputs[:i]]:
            if output_path.resolve() == other.resolve() or (
                output_path.exists() and other.exists() and output_path.samefile(other)
            ):
                raise InputError("Выходной файл не должен совпадать с входным или другим выходным")


def write_result(data: dict, output: str | None) -> None:
    result = json_text(data)
    if output:
        Path(output).write_text(result, encoding="utf-8")
    else:
        sys.stdout.write(result)


def run_generate(args: argparse.Namespace, source: Source) -> None:
    stream = source.generate(args.seed)
    finite = args.n is not None and args.n > 0
    if finite:
        stream = islice(stream, args.n)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as output:
            for symbol in stream:
                output.write(json.dumps(symbol, ensure_ascii=False) + "\n")
    else:
        for symbol in stream:
            print(json.dumps(symbol, ensure_ascii=False), flush=not finite)


def run_analyze(args: argparse.Namespace, source: Source) -> None:
    word = args.word if args.word_file is None else read_json(args.word_file)
    if not isinstance(word, list) or not word or any(not isinstance(a, str) or not a for a in word):
        raise InputError("Блок: ожидается непустой JSON-массив непустых строк")
    write_result(analyze(source, word, args.n, args.seed), args.output)


def run_entropy(args: argparse.Namespace, source: Source) -> None:
    distribution = iid_distribution(source)
    data = {"stationary": True, "memoryless": True,
            "distribution": {a: fraction_text(p) for a, p in distribution.items()},
            "entropy_bits": str(entropy(distribution))}
    write_result(data, args.output)


def run_uniform(args: argparse.Namespace, source: Source) -> None:
    distribution = iid_distribution(source)
    rate = None if args.rate.upper() == "H" else probability(args.rate, "R")
    epsilon = probability(args.epsilon, "ε")
    data, description = analyze_uniform(distribution, rate, epsilon, args.q, args.n_max)
    # Сериализуем оба результата до записи, чтобы ошибка JSON не оставила полукод.
    result = json_text(data)
    code_text = json_text(description)
    Path(args.code_output).write_text(code_text, encoding="utf-8")
    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
    else:
        sys.stdout.write(result)


def run(args: argparse.Namespace, argument_parser: argparse.ArgumentParser) -> None:
    if args.variant:
        write_result(VARIANT.as_dict(), None)
        return
    if args.command is None:
        argument_parser.error("Укажите команду или --variant; список команд: --help")
    if args.command in {"compress", "decompress"}:
        operation = compress if args.command == "compress" else decompress
        data = operation(args.source, args.output)
        if not args.stats:
            data = {key: value for key, value in data.items() if key in {"output", "verified"}}
        write_result(data, None)
        return
    check_output_paths(args)
    source = Source.load(args.source)
    handlers = {"generate": run_generate, "analyze": run_analyze,
                "entropy": run_entropy, "uniform": run_uniform}
    handlers[args.command](args, source)


def main(argv: list[str] | None = None) -> int:
    argument_parser = parser()
    args = argument_parser.parse_args(argv)
    try:
        run(args, argument_parser)
    except KeyboardInterrupt:
        print("Остановлено пользователем (Ctrl+C)", file=sys.stderr)
        return 130
    except BrokenPipeError:
        # Не допускать повторной ошибки при завершении stdout после head.
        import os
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        return 1
    except (InputError, OSError, UnicodeError) as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 2
    return 0
