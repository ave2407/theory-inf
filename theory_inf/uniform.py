# BEGIN GENERATED CODE: OpenAI Codex; назначение и происхождение — SOURCES.md.
"""Равномерное кодирование iid-источника точным методом типов."""

from fractions import Fraction
from math import comb, lcm

from theory_inf.distributions import InputError, fraction_text
from theory_inf.experiment import fraction_record
from theory_inf.information import code_length, entropy, log_ratio, rate_relation


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
        """Распределить оставшиеся позиции между символами с индексами i и выше."""
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
    """Ответить, будет ли P_e(n)≤ε для всех достаточно больших n.

    Результат содержит логический ответ и обоснование. Конечная таблица
    не используется: разбираются R относительно H, точная нулевая ошибка
    и округление длины при R=H. rate=None задаёт точное равенство R=H.
    """
    support = sum(p > 0 for p in distribution.values())
    relation = rate_relation(rate, distribution)
    if epsilon == Fraction(1) or support == 1:
        return {"eventually_below_epsilon": True, "reason": "Ошибка всегда не больше ε"}
    if epsilon == Fraction(0):
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
    """Вернуть таблицу оптимальных ошибок и отдельное описание построенного кода.

    Для n=1,…,n_max вычисляются длина слова, число выбранных блоков и P_e.
    minimum_n относится только к этому отрезку; асимптотический ответ
    вычисляется отдельно. Второй словарь задаёт порядок блоков и кодовых слов,
    позволяющий восстановить код без сохранения экспоненциальной кодовой книги.
    """
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

# END GENERATED CODE: OpenAI Codex.
