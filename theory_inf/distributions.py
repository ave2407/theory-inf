# BEGIN GENERATED CODE: OpenAI Codex; назначение и происхождение — SOURCES.md.
"""Точная арифметика вероятностей и выборка без округления в float."""

from bisect import bisect_right
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from math import lcm
import random
import re


class InputError(ValueError):
    """Ошибка пользовательских данных с готовым диагностическим сообщением."""


def fraction_text(value: Fraction) -> str:
    """Записать точную дробь как «a/b» или целое, включая числа длиннее 4300 цифр."""
    # Decimal(int) точен и обходит ограничение str(int) на 4300 цифр.
    numerator = str(Decimal(value.numerator))
    return numerator if value.denominator == 1 else numerator + "/" + str(Decimal(value.denominator))


def object_map(value: object, location: str) -> dict:
    """Проверить непустой объект с непустыми строковыми ключами; location — путь ошибки."""
    if not isinstance(value, dict) or not value:
        raise InputError(f"{location}: ожидается непустой JSON-объект")
    if any(not isinstance(key, str) or not key for key in value):
        raise InputError(f"{location}: имена должны быть непустыми строками")
    return value


def fields(data: dict, required: set[str], optional: set[str], location: str) -> None:
    """Отвергнуть отсутствующие обязательные и неизвестные поля JSON-объекта."""
    missing = required - data.keys()
    extra = data.keys() - required - optional
    if missing:
        raise InputError(f"{location}: отсутствуют поля {', '.join(sorted(missing))}")
    if extra:
        raise InputError(f"{location}: неизвестные поля {', '.join(sorted(extra))}")


def probability(value: object, location: str) -> Fraction:
    """Разобрать строку с неотрицательной дробью без промежуточного float.

    Верхняя граница 1 здесь не проверяется: этот же разбор используется для R.
    Нормировку вероятностей проверяет Distribution.parse.
    """
    if not isinstance(value, str):
        raise InputError(f"{location}: вероятность должна быть строкой")
    value = value.strip()
    if not re.fullmatch(r"[+-]?(?:\d+/\d+|\d+(?:\.\d*)?|\.\d+)", value):
        raise InputError(f"{location}: ожидается дробь или десятичная запись")
    try:
        result = Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise InputError(f"{location}: некорректная вероятность {value!r}") from exc
    if result < 0:
        raise InputError(f"{location}: отрицательная вероятность")
    return result


@dataclass(frozen=True)
class Distribution:
    """Точное дискретное распределение и целые веса для случайной выборки.

    probabilities хранит все вероятности, включая нулевые. outcomes содержит
    только возможные исходы; cumulative — правые границы их интервалов билетов,
    total — число билетов. Например, для (A:1/3, B:2/3) границы равны (1,3).
    Один класс описывает выбор символа, модели или следующего состояния.
    """
    probabilities: dict[str, Fraction]
    outcomes: tuple[str, ...]
    cumulative: tuple[int, ...]
    total: int

    @classmethod
    def parse(cls, value: object, location: str) -> "Distribution":
        """Проверить сумму 1 и перевести дроби в целые веса с общим знаменателем."""
        data = object_map(value, location)
        probabilities = {
            key: probability(data[key], f"{location}.{key}") for key in sorted(data)
        }
        if sum(probabilities.values()) != 1:
            raise InputError(f"{location}: сумма вероятностей должна равняться 1")
        denominator = lcm(*(p.denominator for p in probabilities.values()))
        outcomes = []
        cumulative = []
        total = 0
        for key, p in probabilities.items():
            if p:
                outcomes.append(key)
                total += p.numerator * (denominator // p.denominator)
                cumulative.append(total)
        return cls(probabilities, tuple(outcomes), tuple(cumulative), total)

    def draw(self, rng: random.Random) -> str:
        """Выбрать исход целым билетом из [0,total); единственный исход не тратит RNG."""
        if len(self.outcomes) == 1:
            return self.outcomes[0]
        return self.outcomes[bisect_right(self.cumulative, rng.randrange(self.total))]


def references(distribution: Distribution, names: set[str], location: str) -> None:
    """Убедиться, что все имена исходов объявлены среди моделей или состояний."""
    unknown = distribution.probabilities.keys() - names
    if unknown:
        raise InputError(f"{location}: неизвестные ссылки {', '.join(sorted(unknown))}")

# END GENERATED CODE: OpenAI Codex.
