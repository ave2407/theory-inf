"""Энтропия, сравнение скоростей и надёжное округление длины кодового слова."""

from decimal import Decimal, ROUND_FLOOR, localcontext
from fractions import Fraction

from theory_inf.distributions import InputError


def decimal_fraction(value: Fraction) -> Decimal:
    """Преобразовать дробь в Decimal с точностью текущего decimal-контекста."""
    return Decimal(value.numerator) / Decimal(value.denominator)


def rational_log(value: Fraction) -> int | None:
    """log2(value), если value — целая степень двойки."""
    n, d = value.numerator, value.denominator
    if n > 0 and n & (n - 1) == 0 and d & (d - 1) == 0:
        return n.bit_length() - d.bit_length()
    return None


def exact_entropy(distribution: dict[str, Fraction]) -> Fraction | None:
    """Вычислить H точно, если все ненулевые p — степени двойки; иначе вернуть None."""
    total = Fraction(0)
    for p in distribution.values():
        if p:
            exponent = rational_log(p)
            if exponent is None:
                return None
            total -= p * exponent
    return total


def entropy(distribution: dict[str, Fraction], precision: int = 80) -> Decimal:
    """Вычислить H=−Σ p·log₂p в битах с precision значащими цифрами.

    Нулевые вероятности пропускаются. Дополнительная внутренняя точность
    сохраняет различие очень близких к единице вероятностей; результат
    округляется до precision. Ожидается непустое нормированное распределение.
    """
    with localcontext() as context:
        # Сохраняем отличие (D−1)/D от единицы даже при D > 10**precision.
        guard = max(Decimal(p.denominator).adjusted() + 1 for p in distribution.values())
        context.prec = precision + guard
        exact = exact_entropy(distribution)
        if exact is not None:
            result = decimal_fraction(exact)
        else:
            result = -sum((decimal_fraction(p) * decimal_fraction(p).ln() / Decimal(2).ln()
                           for p in distribution.values() if p), Decimal(0))
        context.prec = precision
        return +result


def log_ratio(numerator: int, denominator: int) -> Fraction | None:
    """Рациональное log_denominator(numerator), иначе None; без float."""
    if numerator == 1:
        return Fraction(0)
    rest, prime = numerator, 2
    ratios = []
    other = denominator
    while prime * prime <= rest:
        if rest % prime:
            prime += 1
            continue
        a = b = 0
        while rest % prime == 0:
            rest //= prime
            a += 1
        while other % prime == 0:
            other //= prime
            b += 1
        if not b:
            return None
        ratios.append(Fraction(a, b))
        prime += 1
    if rest > 1:
        b = 0
        while other % rest == 0:
            other //= rest
            b += 1
        if not b:
            return None
        ratios.append(Fraction(1, b))
    if other != 1 or len(set(ratios)) != 1:
        return None
    return ratios[0]


def rate_relation(rate: Fraction | None, distribution: dict[str, Fraction]) -> int:
    """Вернуть знак R−H: −1, 0 или 1; rate=None обозначает точное R=H.

    Если H не получается вычислить рационально, точность повышается до
    надёжного различения. Неразличимые значения дают InputError, а не
    приближённое равенство по допуску.
    """
    if rate is None:
        return 0
    exact = exact_entropy(distribution)
    if exact is not None:
        return (rate > exact) - (rate < exact)
    for precision in (80, 160, 320):
        with localcontext() as context:
            context.prec = precision
            difference = decimal_fraction(rate) - entropy(distribution, precision)
            if abs(difference) > Decimal(10) ** (-precision + 10):
                return 1 if difference > 0 else -1
    raise InputError("Не удаётся различить R и H с точностью 320 знаков; для точного R=H используйте --rate H")


def code_length(n: int, rate: Fraction | None, distribution: dict[str, Fraction], q: int) -> int:
    """Вычислить ℓ=floor(n·R/log₂(q)); rate=None обозначает точное R=H.

    Рациональные случаи округляются точно; остальные — через Decimal
    с повышением точности у целой границы. Если округление не удаётся
    надёжно определить, возникает InputError.
    """
    if rate == 0:
        return 0
    exact = exact_entropy(distribution) if rate is None else rate
    log_q = rational_log(Fraction(q))
    if exact is not None and log_q is not None:
        value = n * exact / log_q
        return value.numerator // value.denominator
    positive = [p for p in distribution.values() if p]
    if rate is None and len(set(positive)) == 1:
        ratio = log_ratio(len(positive), q)
        if ratio is not None:
            value = n * ratio
            return value.numerator // value.denominator
    for precision in (80, 160, 320):
        with localcontext() as context:
            context.prec = precision
            r = entropy(distribution, precision) if rate is None else decimal_fraction(rate)
            value = n * r * Decimal(2).ln() / Decimal(q).ln()
            lower = int(value.to_integral_value(rounding=ROUND_FLOOR))
            distance = min(value - lower, lower + 1 - value)
            if distance > Decimal(10) ** (-precision + max(10, value.adjusted() + 10)):
                return lower
    # Нулевая скорость даёт точное нулевое значение при любом q.
    if (rate == 0) or (rate is None and len(positive) == 1):
        return 0
    raise InputError("Не удалось надёжно округлить длину кода с точностью 320 знаков")
