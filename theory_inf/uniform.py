"""Равномерное кодирование iid-источника: проверка закона и точный метод типов."""

from collections import deque
from decimal import Decimal, ROUND_FLOOR, localcontext
from fractions import Fraction
from math import comb, lcm

from theory_inf.distributions import InputError, fraction_text
from theory_inf.experiment import fraction_record
from theory_inf.source import Source


class LinearSpan:
    """Базис методом Гаусса. add возвращает True только для нового направления.

    Линейные равенства достаточно проверять на базисе: для любой линейной
    комбинации они выполнятся автоматически. Это завершает проверку потока
    после конечного числа векторов вместо перебора всех префиксов.
    """

    def __init__(self):
        self.rows: dict[int, list[Fraction]] = {}

    def add(self, vector: list[Fraction]) -> bool:
        reduced = vector.copy()
        for pivot, row in sorted(self.rows.items()):
            if reduced[pivot]:
                weight = reduced[pivot]
                reduced = [a - weight * b for a, b in zip(reduced, row)]
        for pivot, weight in enumerate(reduced):
            if weight:
                self.rows[pivot] = [a / weight for a in reduced]
                return True
        return False


def iid_distribution(source: Source) -> dict[str, Fraction]:
    """Проверить iid-закон на всём потоке, а не на фиксированном числе тактов.

    Координата вектора — масса пары (состояние, фаза). step(v, a) переносит
    её после выдачи a; сумма координат равна вероятности префикса с a.
    Для iid должно быть sum(step(v, a)) == sum(v) * P(a) для любого
    достижимого v. Операции линейны, поэтому достаточно достижимого базиса.
    """
    states = sorted(source.schedules)
    indices = {(state, phase): i for i, (state, phase) in
               enumerate((s, p) for s in states for p in range(source.period))}
    dimension = len(indices)
    initial = [Fraction(0)] * dimension
    for state, weight in source.initial.probabilities.items():
        initial[indices[state, 0]] = weight
    edges = {a: [[] for _ in range(dimension)] for a in source.alphabet}
    for (state, phase), i in indices.items():
        emissions = source.emissions[source.schedules[state][phase]]
        for a in source.alphabet:
            for next_state, weight in source.transitions[state][a].probabilities.items():
                mass = emissions[a] * weight
                if mass:
                    edges[a][i].append((indices[next_state, (phase + 1) % source.period], mass))

    def step(vector: list[Fraction], symbol: str | None = None) -> list[Fraction]:
        result = [Fraction(0)] * dimension
        for a in source.alphabet if symbol is None else (symbol,):
            for i, mass in enumerate(vector):
                if mass:
                    for j, weight in edges[a][i]:
                        result[j] += mass * weight
        return result

    distribution = {a: sum(step(initial, a)) for a in source.alphabet}
    # Если все односимвольные законы одинаковы, но iid не выполнено,
    # нарушена независимость. Иначе можно сразу указать нестационарность.
    marginals = LinearSpan()
    vector = initial
    time = 1
    while marginals.add(vector):
        if any(sum(step(vector, a)) != distribution[a] for a in source.alphabet):
            raise InputError(f"Источник нестационарен: распределение символа меняется на такте {time}")
        vector = step(vector)
        time += 1

    reachable = LinearSpan()
    reachable.add(initial)
    queue = deque([(initial, ())])
    while queue:
        vector, prefix = queue.popleft()
        mass = sum(vector)
        for a in source.alphabet:
            following = step(vector, a)
            if sum(following) != mass * distribution[a]:
                raise InputError(
                    f"Источник имеет память: вероятность {a!r} зависит от префикса {list(prefix)!r}"
                )
            if any(following) and reachable.add(following):
                queue.append((following, (*prefix, a)))
    return distribution


def decimal_fraction(value: Fraction) -> Decimal:
    return Decimal(value.numerator) / Decimal(value.denominator)


def rational_log(value: Fraction) -> int | None:
    """log2(value), если value — целая степень двойки."""
    n, d = value.numerator, value.denominator
    if n > 0 and n & (n - 1) == 0 and d & (d - 1) == 0:
        return n.bit_length() - d.bit_length()
    return None


def exact_entropy(distribution: dict[str, Fraction]) -> Fraction | None:
    total = Fraction(0)
    for p in distribution.values():
        if p:
            exponent = rational_log(p)
            if exponent is None:
                return None
            total -= p * exponent
    return total


def entropy(distribution: dict[str, Fraction], precision: int = 80) -> Decimal:
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
    """None обозначает точно R=H; численное равенство не вводится допуском."""
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
    """ℓ = floor(n·R/log₂(q)); rate=None обозначает точное R=H."""
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


def block_types(weights: tuple[int, ...], n: int) -> list[tuple[int, tuple[int, ...], int]]:
    """Вернуть (числитель P одного блока, тип, число блоков этого типа).

    Если p_i = weights[i]/D, у типа (n_1,...,n_k) вероятность каждого
    блока равна ∏weights[i]**n_i / D**n, мощность — n!/(n_1!···n_k!).
    Сортировка идёт по вероятности одного блока, а не сумме по типу.
    """
    powers = [[w ** i for i in range(n + 1)] for w in weights]
    result = []

    def visit(i: int, remaining: int, probability_numerator: int,
              multiplicity: int, counts: tuple[int, ...]):
        if i == len(weights) - 1:
            result.append((probability_numerator * powers[i][remaining],
                           (*counts, remaining), multiplicity))
            return
        for count in range(remaining + 1):
            # Из ещё свободных позиций выбираем count мест для символа i.
            visit(i + 1, remaining - count, probability_numerator * powers[i][count],
                  multiplicity * comb(remaining, count), (*counts, count))

    visit(0, n, 1, 1, ())
    result.sort(key=lambda item: (-item[0], item[1]))
    return result


def optimal_error(distribution: dict[str, Fraction], n: int, q: int, length: int) -> tuple[Fraction, int]:
    """Выбрать до q**length наиболее вероятных блоков; вернуть (P_e, их число)."""
    positive = [p for p in distribution.values() if p]
    total_blocks = len(positive) ** n
    # Не вычислять q**length, когда уже известно, что все блоки помещаются.
    sufficient = 0
    bound = 1
    while bound < total_blocks:
        bound *= q
        sufficient += 1
    if length >= sufficient:
        return Fraction(0), total_blocks
    capacity = q ** length
    denominator = lcm(*(p.denominator for p in positive))
    weights = tuple(p.numerator * (denominator // p.denominator) for p in positive)
    remaining = capacity
    covered_numerator = 0
    for probability_numerator, _, multiplicity in block_types(weights, n):
        taken = min(remaining, multiplicity)
        covered_numerator += taken * probability_numerator
        remaining -= taken
        if not remaining:
            break
    block_denominator = denominator ** n
    return Fraction(block_denominator - covered_numerator, block_denominator), capacity


def asymptotic(distribution: dict[str, Fraction], rate: Fraction | None,
               epsilon: Fraction, q: int) -> dict:
    support = sum(p > 0 for p in distribution.values())
    relation = rate_relation(rate, distribution)
    if epsilon == 1 or support == 1:
        return {"eventually_below_epsilon": True, "reason": "Ошибка всегда не больше ε"}
    if epsilon == 0:
        uniform = {a: Fraction(1, support) for a, p in distribution.items() if p}
        relation_to_support = rate_relation(rate, uniform) if rate is not None else (
            0 if len({p for p in distribution.values() if p}) == 1 else -1)
        ratio = log_ratio(support, q)
        yes = relation_to_support > 0 or (relation_to_support == 0 and ratio is not None and ratio.denominator == 1)
        return {"eventually_below_epsilon": yes,
                "reason": "Для ε=0 должны помещаться все блоки положительной вероятности: q^ℓ ≥ |support|^n"}
    if relation:
        return {"eventually_below_epsilon": relation > 0,
                "reason": "R>H: P_e(n)→0" if relation > 0 else
                          "R<H: P_e(n)→1; подходящие малые n этим не исключаются"}
    positive = [p for p in distribution.values() if p]
    if len(set(positive)) != 1:
        return {"eventually_below_epsilon": epsilon >= Fraction(1, 2),
                "reason": "R=H, неравномерный iid-источник: P_e→1/2; при ε=1/2 достаточность следует из поправки −(log₂ n)/2 к log₂ M*(n,ε)"}
    ratio = log_ratio(support, q)
    if ratio is None:
        yes = epsilon >= Fraction(q - 1, q)
        reason = "R=H, равномерный источник: дробные части n·log_q(|support|) плотны; sup P_e=1−1/q"
    else:
        b = ratio.denominator
        yes = (1 - epsilon) ** b * q ** (b - 1) <= 1
        reason = f"R=H, равномерный источник: период округления {b}; max P_e=1−q^(-({b}−1)/{b})"
    return {"eventually_below_epsilon": yes, "reason": reason}


def analyze_uniform(distribution: dict[str, Fraction], rate: Fraction | None,
                    epsilon: Fraction, q: int, n_max: int) -> tuple[dict, dict]:
    if rate is not None and rate < 0:
        raise InputError("R должен быть неотрицательным")
    if not 0 <= epsilon <= 1:
        raise InputError("ε должен находиться в [0,1]")
    if q < 2 or n_max < 1:
        raise InputError("Требуются q>=2 и n_max>=1")
    table = []
    for n in range(1, n_max + 1):
        length = code_length(n, rate, distribution, q)
        error, selected = optimal_error(distribution, n, q, length)
        table.append({"n": n, "length": length, "selected_blocks": selected,
                      "error": fraction_record(error), "meets_epsilon": error <= epsilon})
    result = {
        "distribution": {a: fraction_text(p) for a, p in distribution.items()},
        "entropy_bits": str(entropy(distribution)),
        "rate": "H" if rate is None else fraction_text(rate), "q": q, "epsilon": fraction_text(epsilon),
        "n_max": n_max, "table": table,
        "minimum_n": next((row["n"] for row in table if row["meets_epsilon"]), None),
        "finite_interval_note": "minimum_n=null означает отсутствие подходящего n только на [1,n_max]",
        "asymptotic": asymptotic(distribution, rate, epsilon, q),
    }
    description = {
        "format": "uniform-types-v1",
        "alphabet": [a for a, p in distribution.items() if p],
        "distribution": result["distribution"], "rate": result["rate"], "q": q,
        "ordering": [
            "Для каждого n перечислить типы (n_1,...,n_k) по алфавиту положительной вероятности.",
            "Сортировать по убыванию ∏p_i^n_i; при равенстве — по возрастанию вектора типа.",
            "Внутри типа сортировать блоки лексикографически по alphabet.",
            "Взять первые selected_blocks блоков; нулевые вероятности не кодируются.",
            "Блоку с рангом j от 0 назначить q-ичную запись j, дополненную нулями слева до length.",
            "При length=0 единственное кодовое слово — пустой массив цифр.",
            "Цифры кодового алфавита — целые числа 0,...,q−1; кодовое слово — массив цифр.",
            "Обратное отображение: q-ичное слово → ранг → блок в том же порядке; неиспользованный ранг — ошибка.",
        ],
        "blocks": [{key: row[key] for key in ("n", "length", "selected_blocks")} for row in table],
    }
    return result, description
