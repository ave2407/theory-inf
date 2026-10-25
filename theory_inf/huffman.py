# BEGIN GENERATED CODE: OpenAI Codex; назначение и происхождение — SOURCES.md.
"""Хаффман: две очереди, массив родителей и канонические коды по длинам."""

from typing import BinaryIO

from theory_inf.distributions import InputError


def code_lengths(frequencies: list[int]) -> dict[int, int]:
    """Построить оптимальные длины за O(m log m) времени и O(m) памяти.

    Листья отсортированы один раз. Веса создаваемых узлов не убывают,
    поэтому достаточно голов двух очередей: листьев и внутренних узлов.
    Родитель всегда создан позже ребёнка; глубины вычисляются обратным проходом.
    При равном весе лист предшествует внутреннему узлу, листья — по байту,
    внутренние узлы — по порядку создания. Один символ имеет длину 0.
    """
    if len(frequencies) != 256 or any(type(n) is not int or n < 0 for n in frequencies):
        raise InputError("Нужны 256 неотрицательных целых частот байтов")
    leaves = sorted((weight, symbol) for symbol, weight in enumerate(frequencies) if weight)
    count = len(leaves)
    if count < 2:
        return {symbol: 0 for _, symbol in leaves}
    weights = [weight for weight, _ in leaves]
    parents = [-1] * count
    leaf_head, branch_head = 0, count

    def take_minimum() -> int:
        nonlocal leaf_head, branch_head
        if leaf_head < count and (branch_head == len(weights) or
                                  weights[leaf_head] <= weights[branch_head]):
            result = leaf_head
            leaf_head += 1
        else:
            result = branch_head
            branch_head += 1
        return result

    for _ in range(count - 1):
        first, second = take_minimum(), take_minimum()
        parent = len(weights)
        parents[first] = parents[second] = parent
        weights.append(weights[first] + weights[second])
        parents.append(-1)
    depths = [0] * len(weights)
    for node in range(len(weights) - 2, -1, -1):
        depths[node] = depths[parents[node]] + 1
    return {symbol: depths[i] for i, (_, symbol) in enumerate(leaves)}


def canonical_codes(lengths: dict[int, int]) -> dict[int, tuple[int, int]]:
    """Распределить интервалы кодов по длинам; вернуть байт → (число, длина).

    Сначала проверяется число свободных мест на каждом уровне (равенство
    Крафта). Затем символы каждой длины занимают последовательные номера.
    Порядок байтов внутри уровня определён форматом ZMH1.
    """
    if any(type(a) is not int or not 0 <= a <= 255 or
           type(n) is not int or not 0 <= n <= 255 for a, n in lengths.items()):
        raise InputError("Некорректный символ или длина кода")
    if not lengths:
        return {}
    if len(lengths) == 1:
        symbol, length = next(iter(lengths.items()))
        if length != 0:
            raise InputError("Единственный символ должен иметь код длины 0")
        return {symbol: (0, 0)}
    if 0 in lengths.values():
        raise InputError("Нулевая длина разрешена только для единственного символа")
    levels = [[] for _ in range(max(lengths.values()) + 1)]
    for symbol in sorted(lengths):
        levels[lengths[symbol]].append(symbol)
    free = 1
    first_code = 0
    result = {}
    for width in range(1, len(levels)):
        free = 2 * free - len(levels[width])
        if free < 0:
            raise InputError("Переполненное кодовое дерево")
        first_code *= 2
        for offset, symbol in enumerate(levels[width]):
            result[symbol] = (first_code + offset, width)
        first_code += len(levels[width])
    if free:
        raise InputError("Неполное кодовое дерево")
    return result


class BitWriter:
    """Потоковый MSB-first вывод с заполнением одного байта по частям.

    Незаконченный байт хранится выровненным влево. Кодовое слово разбивается
    на куски по свободному месту в этом байте; большие битовые хвосты не хранятся.
    """

    def __init__(self, stream: BinaryIO, buffer_size: int = 65536):
        if buffer_size < 1:
            raise InputError("Размер буфера должен быть положительным")
        self.stream = stream
        self.buffer_size = buffer_size
        self.buffer = bytearray()
        self.byte = self.used = self.total_bits = 0

    def write(self, code: int, length: int) -> None:
        """Записать проверенное слово, выделяя не более восьми битов за шаг."""
        self.total_bits += length
        remaining = length
        while remaining:
            take = min(8 - self.used, remaining)
            remaining -= take
            part = (code >> remaining) & ((1 << take) - 1)
            self.byte |= part << (8 - self.used - take)
            self.used += take
            if self.used == 8:
                self.buffer.append(self.byte)
                self.byte = self.used = 0
                if len(self.buffer) >= self.buffer_size:
                    self.stream.write(self.buffer)
                    self.buffer.clear()

    def finish(self) -> None:
        """Дополнить последний байт нулями справа и сбросить буфер."""
        if self.used:
            self.buffer.append(self.byte)
        self.stream.write(self.buffer)
        self.buffer.clear()
        self.byte = self.used = 0

# END GENERATED CODE: OpenAI Codex.
