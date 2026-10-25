"""Частоты перекрывающихся блоков в одной реализации, без хранения всего потока."""

from fractions import Fraction
from collections.abc import Iterable, Sequence

from theory_inf.distributions import InputError, fraction_text
from theory_inf.source import Source

TABLE_LENGTHS = (100, 1_000, 10_000, 100_000, 1_000_000)


def frequencies(
    stream: Iterable[str], word: Sequence[str], checkpoints: Sequence[int],
) -> dict[int, Fraction | None]:
    if not word:
        raise InputError("Блок должен содержать хотя бы один символ")
    if not checkpoints or any(type(n) is not int or n <= 0 for n in checkpoints):
        raise InputError("Длины реализации должны быть положительными целыми числами")
    # KMP считает перекрытия за O(N+r), включая длинные блоки из одного символа.
    prefix = [0] * len(word)
    matched = 0
    for i in range(1, len(word)):
        while matched and word[i] != word[matched]:
            matched = prefix[matched - 1]
        if word[i] == word[matched]:
            matched += 1
        prefix[i] = matched
    wanted = set(checkpoints)
    end = max(wanted)
    matched = count = 0
    result = {}
    for n, symbol in enumerate(stream, 1):
        while matched and symbol != word[matched]:
            matched = prefix[matched - 1]
        if symbol == word[matched]:
            matched += 1
        if matched == len(word):
            count += 1
            matched = prefix[matched - 1]
        if n in wanted:
            result[n] = Fraction(count, n - len(word) + 1) if n >= len(word) else None
        if n == end:
            return result
    raise InputError("Реализация закончилась раньше последней контрольной точки")


def fraction_record(value: Fraction | None) -> dict | None:
    if value is None:
        return None
    return {"fraction": fraction_text(value), "decimal": float(value)}


def analyze(source: Source, word: Sequence[str], n: int, seed: int) -> dict:
    if not word:
        raise InputError("Блок должен содержать хотя бы один символ")
    if n <= 0 or n < len(word):
        raise InputError("Для частоты требуется N >= длины блока и N > 0")
    first, average = source.exact_probabilities(word)
    measured = frequencies(source.generate(seed), word, (*TABLE_LENGTHS, n))
    return {
        "seed": seed,
        "word": list(word),
        "N": n,
        "exact_first": fraction_record(first),
        "exact_period_average": fraction_record(average),
        "frequency": fraction_record(measured[n]),
        "table": [
            {
                "N": size,
                "frequency": fraction_record(measured[size]),
                "error_first": fraction_record(abs(measured[size] - first)) if measured[size] is not None else None,
                "error_period_average": fraction_record(abs(measured[size] - average)) if measured[size] is not None else None,
            }
            for size in TABLE_LENGTHS
        ],
        "note": (
            "Таблица использует префиксы одной реализации. null: N меньше длины блока. "
            "Для исходного формата частота сходится к среднему по периоду; "
            "для неэргодического расширения общий ансамблевый предел не гарантирован."
        ),
    }
