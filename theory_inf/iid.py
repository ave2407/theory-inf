# BEGIN GENERATED CODE: OpenAI Codex; назначение и происхождение — SOURCES.md.
"""Точная проверка стационарного источника без памяти, включая скрытые состояния."""

from collections import deque
from fractions import Fraction

from theory_inf.distributions import InputError
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
        """Добавить независимый вектор и вернуть True; зависимый даёт False.

        Исходный вектор не меняется. В rows хранится нормированная строка
        для каждого ведущего столбца: её первый ненулевой элемент равен 1.
        """
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
        """Перенести массы на такт с заданным символом или суммой по всем символам."""
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

# END GENERATED CODE: OpenAI Codex.
