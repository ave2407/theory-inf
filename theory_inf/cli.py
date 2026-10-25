"""Неинтерактивные режимы задачи 1.1."""

import argparse
from itertools import islice
import json
from pathlib import Path
import sys

from theory_inf.distributions import InputError
from theory_inf.experiment import analyze
from theory_inf.source import Source, read_json
from theory_inf.variant import VARIANT


def length(value: str) -> int | None:
    if value.lower() == "none":
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Ожидается целое N или None") from exc


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Теория информации, ДЗ №1, задача 1.1")
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
    return result


def run(args: argparse.Namespace, argument_parser: argparse.ArgumentParser) -> None:
    if args.variant:
        print(json.dumps(VARIANT.as_dict(), ensure_ascii=False, indent=2))
        return
    if args.command is None:
        argument_parser.error("Укажите generate, analyze или --variant")
    if args.output:
        output_path = Path(args.output)
        inputs = [args.source]
        if args.command == "analyze" and args.word_file:
            inputs.append(args.word_file)
        for input_path in map(Path, inputs):
            if output_path.resolve() == input_path.resolve() or (
                output_path.exists() and input_path.exists() and output_path.samefile(input_path)
            ):
                raise InputError("Выходной файл не должен совпадать с входным")
    source = Source.load(args.source)
    if args.command == "analyze":
        word = args.word if args.word_file is None else read_json(args.word_file)
        if not isinstance(word, list) or not word or any(not isinstance(a, str) or not a for a in word):
            raise InputError("Блок: ожидается непустой JSON-массив непустых строк")
        result = json.dumps(analyze(source, word, args.n, args.seed), ensure_ascii=False, indent=2) + "\n"
        if args.output:
            with open(args.output, "w", encoding="utf-8") as stream:
                stream.write(result)
        else:
            sys.stdout.write(result)
    else:
        # Проверка до открытия output: вход не должен случайно затереться.
        stream = source.generate(args.seed)
        if args.n is not None and args.n > 0:
            stream = islice(stream, args.n)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as output:
                for symbol in stream:
                    output.write(json.dumps(symbol, ensure_ascii=False) + "\n")
        else:
            for symbol in stream:
                print(json.dumps(symbol, ensure_ascii=False), flush=args.n is None or args.n <= 0)


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
