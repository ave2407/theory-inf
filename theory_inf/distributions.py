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
    # Decimal(int) точен и обходит ограничение str(int) на 4300 цифр.
    numerator = str(Decimal(value.numerator))
    return numerator if value.denominator == 1 else numerator + "/" + str(Decimal(value.denominator))


def object_map(value: object, location: str) -> dict:
    if not isinstance(value, dict) or not value:
        raise InputError(f"{location}: ожидается непустой JSON-объект")
    if any(not isinstance(key, str) or not key for key in value):
        raise InputError(f"{location}: имена должны быть непустыми строками")
    return value


def fields(data: dict, required: set[str], optional: set[str], location: str) -> None:
    missing = required - data.keys()
    extra = data.keys() - required - optional
    if missing:
        raise InputError(f"{location}: отсутствуют поля {', '.join(sorted(missing))}")
    if extra:
        raise InputError(f"{location}: неизвестные поля {', '.join(sorted(extra))}")


def probability(value: object, location: str) -> Fraction:
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
    probabilities: dict[str, Fraction]
    outcomes: tuple[str, ...]
    cumulative: tuple[int, ...]
    total: int

    @classmethod
    def parse(cls, value: object, location: str) -> "Distribution":
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
        if len(self.outcomes) == 1:
            return self.outcomes[0]
        return self.outcomes[bisect_right(self.cumulative, rng.randrange(self.total))]


def references(distribution: Distribution, names: set[str], location: str) -> None:
    unknown = distribution.probabilities.keys() - names
    if unknown:
        raise InputError(f"{location}: неизвестные ссылки {', '.join(sorted(unknown))}")
